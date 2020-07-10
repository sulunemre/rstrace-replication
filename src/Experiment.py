import datetime
import json
import logging
import time
import os
from collections import Counter

from dateutil import parser
from neo4j import GraphDatabase

import Revfinder, ProfileBased
from Util import parseCommitMessage


class Experiment:
    def __init__(self, config):
        self.experimentDateTime = datetime.datetime.now()
        self.configureLogging()
        self.config = config
        self.results = []
        self.pastCommitsWithReviews = [] # Required for RevFinder
        self.profiles = {} # Required for Profile Based Recommendation

        if self.config["method"] == "rstrace+":
            self.connectToDatabase()
        
        logging.info(
            f"Experiment started at {self.experimentDateTime} with configuration: {self.config}")

    def configureLogging(self):
        logging.basicConfig(
            level=logging.INFO,
            filename=("logs/log-{date:%Y-%m-%d_%H.%M.%S}__" + str(os.getpid()) + ".txt").format(date=self.experimentDateTime),
            force=True)

    def connectToDatabase(self):
        uri = self.config["neo4j"]["uri"]
        user = self.config["neo4j"]["user"]
        password = self.config["neo4j"]["password"]
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

        self.eraseDatabase()
        self.createIndexOnFile()

    def closeDriver(self):
        self.driver.close()
        logging.info("Neo4j driver closed")

    def eraseDatabase(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE (n)")

    def createIndexOnFile(self):
        with self.driver.session() as session:
            session.run("CREATE INDEX ON :File(id)")

    def readCommits(self):
        commitsFilePath = self.config["dataset"]["commitsFilePath"]
        if self.config["dataset"]["type"] == "revrec":
            with open(commitsFilePath, encoding="utf-8") as file:
                self.commits = json.load(file)
                self.commits.reverse() # Data from rev-rec is descending in timestamp so reverse it

        else:
            with open(commitsFilePath, encoding="utf-8") as file:
                commits = []
                for line in file:
                    commits.append(json.loads(line))
                self.commits = commits

    def run(self):
        try:
            self.readCommits()
            self.analyzeCommits()
            self.saveResults()
        finally:
            if self.config["method"] == "rstrace+":
                self.closeDriver()

    def updatePastCommitsWithReviews(self, commit):
        if len(commit["reviewers"]) > 0:
            self.pastCommitsWithReviews.append(commit)

    def updateProfiles(self, commit):
        commitMultiset = ProfileBased.getMultisetFromCommit(commit)
        for reviewer in commit["reviewers"]:
            if reviewer in self.profiles:
                self.profiles[reviewer] |= commitMultiset
            else:
                self.profiles[reviewer] = commitMultiset

    def testCommit(self, commit, i):
        startTime = time.time()
        recommendendReviewers = self.recommendReviewers(commit)
        endTime = time.time()

        elapsedTime = endTime - startTime
        normalizedTime = elapsedTime / len(commit["modifiedFileNames"])

        # Analyze results
        result = self.analyzeRecommendationResults(commit["reviewers"], recommendendReviewers, normalizedTime)
        logging.info(
            f"Commit {i+1} completed; Elapsed time: {elapsedTime} seconds; Commit size: {len(commit['modifiedFileNames'])} files; Actual reviewers: {commit['reviewers']}; Five recommended reviewers: {recommendendReviewers[:5]}; Result: {result}")

    def addCommitToModel(self, commit):
        if self.config["method"] == "rstrace+":
            self.addCommitAndRelationsToDB(commit)
        elif self.config["method"] == "revfinder":
            self.updatePastCommitsWithReviews(commit)
        elif self.config["method"] == "profile-based":
            self.updateProfiles(commit)

    def analyzeCommits(self):
        # Traverse every commit
        datasetType = self.config["dataset"]["type"]
        for i, rawCommit in enumerate(self.commits):
            if datasetType == "revrec":
                commit = self.buildCommitFromRevrecRawCommit(rawCommit)
            elif datasetType == "seoss":
                commit = rawCommit
            elif datasetType == "perceval":
                commit = self.buildCommitFromRawCommit(rawCommit)
            else:
                raise ValueError("datasetType is wrong")
            
            if commit is None:
                continue
            
            if i == 0:
                # Project start date is required for recency calculation
                self.projectStartDate = commit["AuthorDate"]
            
            if len(commit["modifiedFileNames"]) == 0:
                logging.warn(f"No modified files for commit {commit['id']}")
                continue # https://github.com/apache/hive/commit/b41b1065db64c80eb330204e1b6027f0e29a65c4

            # Remove self-reviewers
            if commit["author"] in commit["reviewers"]:
                commit["reviewers"].remove(commit["author"])

            # Test the commit (recommend reviewers and analyze results)
            if len(commit["reviewers"]) > 0:
                self.testCommit(commit, i)

            # Add commit to the model
            self.addCommitToModel(commit)            

    def buildCommitFromRevrecRawCommit(self, rawCommit):
        commit = {}
        commit["id"] = rawCommit["changeId"]
        commit["author"] = rawCommit["owner"]["accountId"]
        commit["modifiedFileNames"] = [x["location"] for x in rawCommit["filePaths"]]
        commit["reviewers"] = [x["accountId"] for x in rawCommit["reviewers"]]
        commit["relatedIssues"] = []
        commit["AuthorDate"] = datetime.datetime.utcfromtimestamp(rawCommit["timestamp"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        
        if len(commit["modifiedFileNames"]) == 0:  # Ignore the commit if no modified files
            logging.warn(f"No modified files for commit {commit['id']}")
            return
        
        return commit

    def buildCommitFromRawCommit(self, rawCommit):
        # Parse commit fields
        commit = rawCommit["data"]
        commitId = commit["commit"]
        commit["id"] = commitId
        author = commit["Author"]
        authorNameWithoutEmail = author.split("<")[0].strip()
        commit["author"] = authorNameWithoutEmail

        files = commit["files"]
        if len(files) == 0:  # Ignore the commit if no modified files
            logging.warn(f"No modified files for commit {commitId}")
            return

        modifiedFileNames = []
        for file in files:
            modifiedFileNames.append(file["file"])
        commit["modifiedFileNames"] = modifiedFileNames

        relatedIssues, reviewers = parseCommitMessage(commit["message"])
        commit["relatedIssues"] = relatedIssues
        commit["reviewers"] = reviewers

        return commit

    def recommendReviewers(self, commit):
        method = self.config["method"]
        if method == "rstrace+":
            with self.driver.session() as session:
                query = self.createCypherQueryFromConfig()
                try:
                    result = session.run(
                        query, projectStartDate=parser.parse(self.projectStartDate, ignoretz=True), endDate=parser.parse(commit["AuthorDate"], ignoretz=True), modifiedFileNames=commit["modifiedFileNames"])
                except:
                    logging.exception("")
                    return []
                recommendedReviewers = [item["developerId"] for item in result]
        
        elif method == "revfinder":
            recommendedReviewers = Revfinder.recommendReviewers(self.pastCommitsWithReviews,commit)
        elif method == 'profile-based':
            recommendedReviewers = ProfileBased.recommendReviewers(self.profiles, commit)
        else:
            raise ValueError(f"Recommendation method {method} is not a valid method")

        # Remove self-reviewer recommendation
        if commit["author"] in recommendedReviewers:
            recommendedReviewers.remove(commit["author"])

        return recommendedReviewers

    def createCypherQueryFromConfig(self):
        query = "MATCH (a:Developer) MATCH (b:File) WHERE b.id IN {modifiedFileNames} "
        pathLengthQuery = ""
        noLoopQuery = "WHERE ALL(x IN NODES(p) WHERE SINGLE(y IN NODES(p) WHERE y = x)) "
        returnQuery = "RETURN a.id AS developerId, "
        orderQuery = "ORDER BY KnowAboutScore DESC"

        if self.config["pathLengthLimit"] == -1:
            pathLengthQuery = "MATCH p  = (a)-[*]->(b) "
        else:
            pathLengthQuery = f"MATCH p = (a)-[*..{self.config['pathLengthLimit']}]->(b) "

        if self.config["recency"] and self.config["squareSum"]:
            knowAboutQuery = "SUM(REDUCE(totalRecency = 1.0, relationship IN relationships(p) | totalRecency * (1 - (1.0 * duration.inDays(COALESCE(relationship.createdAt, {endDate}), {endDate}).days / duration.inDays({projectStartDate}, {endDate}).days))) / (LENGTH(p)) ^ 2) AS KnowAboutScore "
        elif self.config["recency"] and not self.config["squareSum"]:
            knowAboutQuery = "SUM(REDUCE(totalRecency = 1.0, relationship IN relationships(p) | totalRecency * (1 - (1.0 * duration.inDays(COALESCE(relationship.createdAt, {endDate}), {endDate}).days / duration.inDays({projectStartDate}, {endDate}).days))) / LENGTH(p)) AS KnowAboutScore "
        elif not self.config["recency"] and self.config["squareSum"]:
            knowAboutQuery = "SUM(1.0/LENGTH(p) ^ 2) AS KnowAboutScore "
        else:
            knowAboutQuery = "SUM(1.0/LENGTH(p)) AS KnowAboutScore "

        query += pathLengthQuery
        query += noLoopQuery
        query += returnQuery
        query += knowAboutQuery
        query += orderQuery

        return query

    def analyzeRecommendationResults(self, actualReviewers, recommendedReviewers, normalizedTime):
        """
        Calculate top-1 top-3 top-5 and MRR metrics for a given actual reviewers and recommended reviewers list
        :param actualReviewers:
        :param recommendedReviewers:
        :param normalizedTime: time for the recommendation divided by commit size
        """
        try:
            if not recommendedReviewers:
                isFirstRecommended = "N/A"
                inThreeRecommended = "N/A"
                inFiveRecommended = "N/A"
            elif recommendedReviewers[0] in actualReviewers:
                isFirstRecommended = "TRUE"
                inThreeRecommended = "TRUE"
                inFiveRecommended = "TRUE"
            elif recommendedReviewers[1] in actualReviewers or recommendedReviewers[2] in actualReviewers:
                isFirstRecommended = "FALSE"
                inThreeRecommended = "TRUE"
                inFiveRecommended = "TRUE"
            elif recommendedReviewers[3] in actualReviewers or recommendedReviewers[4] in actualReviewers:
                isFirstRecommended = "FALSE"
                inThreeRecommended = "FALSE"
                inFiveRecommended = "TRUE"
            else:
                isFirstRecommended = "FALSE"
                inThreeRecommended = "FALSE"
                inFiveRecommended = "FALSE"
        except IndexError:
            isFirstRecommended = "FALSE"
            inThreeRecommended = "FALSE"
            inFiveRecommended = "FALSE"
        maxMRR = 0
        for actualReviewer in actualReviewers:
            if actualReviewer in recommendedReviewers:
                # Position of actual reviewer in the rec.list
                position = recommendedReviewers.index(actualReviewer) + 1
                mrr = 1.0 / position
            else:  # Does not exist
                mrr = 0

            maxMRR = max(mrr, maxMRR)

        result = (isFirstRecommended, inThreeRecommended, inFiveRecommended, maxMRR, normalizedTime)
        self.results.append(result)
        return result

    def addCommitAndRelationsToDB(self, commit):
        with self.driver.session() as session:
            # Add commit-developer relationship
            session.run("MERGE (a:Developer {id: $author}) MERGE (b:Commit {id: $commitId}) MERGE (a)-[:commits {createdAt: $date}]->(b)",
                        author=commit["author"], commitId=commit["id"], date=parser.parse(commit["AuthorDate"], ignoretz=True))

            # Add commit-file relationship
            for fileName in commit["modifiedFileNames"]:
                session.run("MERGE (a:Commit {id: $commitId}) MERGE (b:File {id: $fileName}) MERGE (a)-[:includes {createdAt: $date}]->(b)",
                            commitId=commit["id"], fileName=fileName, date=parser.parse(commit["AuthorDate"], ignoretz=True))

            # Add commit-issue relationship
            for issueName in commit["relatedIssues"]:
                session.run("MERGE (a:Commit {id: $commitId}) MERGE (b:Issue {id: $issueName}) MERGE (a)-[:implements {createdAt: $date}]->(b)",
                            commitId=commit["id"], issueName=issueName, date=parser.parse(commit["AuthorDate"], ignoretz=True))

            # Add commit-reviewer relationship
            for reviewer in commit["reviewers"]:
                session.run("MERGE (a:Developer {id: $reviewer}) MERGE (b:Commit {id: $commitId}) MERGE (a)-[:reviews {createdAt: $date}]->(b)",
                            commitId=commit["id"], reviewer=reviewer, date=parser.parse(commit["AuthorDate"], ignoretz=True))

    def saveResults(self):
        resultFilePath = ("results/result-{date:%Y-%m-%d_%H.%M.%S}__" + str(os.getpid()) + ".txt").format(
            date=self.experimentDateTime)

        totalResults = len(self.results)
        top1Counter, top3Counter, top5Counter, totalMRR, totalTime = Counter(), Counter(), Counter(), 0, 0
        for result in self.results:
            top1Counter.update(result[0].split())
            top3Counter.update(result[1].split())
            top5Counter.update(result[2].split())
            totalMRR += float(result[3])
            totalTime += float(result[4])

        with open(resultFilePath, "w") as resultFile:
            print(f"Configuration: {self.config}", file=resultFile)
            print(f"Total number of commits: {totalResults}", file=resultFile)

            print(f'top-1 TRUE: {top1Counter["TRUE"]}', file=resultFile)
            print(f'top-1 FALSE: {top1Counter["FALSE"]}', file=resultFile)
            print(f'top-1 N/A: {top1Counter["N/A"]}', file=resultFile)
            print(
                f'top-1 SCORE: {top1Counter["TRUE"] / totalResults}', file=resultFile)

            print(f'top-3 TRUE: {top3Counter["TRUE"]}', file=resultFile)
            print(f'top-3 FALSE: {top3Counter["FALSE"]}', file=resultFile)
            print(f'top-3 N/A: {top3Counter["N/A"]}', file=resultFile)
            print(
                f'top-3 SCORE: {top3Counter["TRUE"] / totalResults}', file=resultFile)

            print(f'top-5 TRUE: {top5Counter["TRUE"]}', file=resultFile)
            print(f'top-5 FALSE: {top5Counter["FALSE"]}', file=resultFile)
            print(f'top-5 N/A: {top5Counter["N/A"]}', file=resultFile)
            print(
                f'top-5 SCORE: {top5Counter["TRUE"] / totalResults}', file=resultFile)

            print(f"MRR: {totalMRR / totalResults}", file=resultFile)
            print(f"Average recommendation time: {totalTime / totalResults}", file=resultFile)
