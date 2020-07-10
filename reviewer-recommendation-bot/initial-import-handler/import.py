from neo4j import GraphDatabase
from perceval.backends.core.git import Git
from perceval.backends.core.github import GitHub
import json
import requests
import shutil
import time

with open('config.json', 'r') as f:
	config = json.load(f)

DB_ADDRESS = config["DB_ADDRESS"]
DB_USERNAME = config["DB_USERNAME"]
DB_PASSWORD = config["DB_PASSWORD"]

GITHUB_REPO_URL = config["GITHUB_REPO_URL"]
GITHUB_REPO_OWNER = config["GITHUB_REPO_OWNER"]  # TODO: parse url and get owner and name
GITHUB_REPO_NAME = config["GITHUB_REPO_NAME"]
GITHUB_API_TOKEN = config["GITHUB_API_TOKEN"]

GITHUB_API_URL = "https://api.github.com"

try:
	driver = GraphDatabase.driver(DB_ADDRESS, auth=(DB_USERNAME, DB_PASSWORD))
except:
	time.sleep(20) # Wait if db is not up
	driver = GraphDatabase.driver(DB_ADDRESS, auth=(DB_USERNAME, DB_PASSWORD))

session = driver.session()

# Clean DB before start
session.run("MATCH (n) DETACH DELETE n")


def add_commits_relation(tx, commit, author):
	print("Adding commits relation: " + str(author) + " " + str(commit))
	tx.run("MERGE (a:Developer {id:$devID}) MERGE (b:Commit {id:$commitID}) MERGE (a)-[:commits]->(b)",
		   devID=author,
		   commitID=commit)


def add_opens_relation(tx, issue, author):
	print("Adding opens relation: " + str(author) + " " + str(issue))
	tx.run("MERGE (a:Developer {id:$devID}) MERGE (b:Issue {id:$issueID}) MERGE (a)-[:opens]->(b)",
		   devID=author,
		   issueID=issue)


def add_proposes_relation(tx, pull_request, author):
	print("Adding proposes relation: " + str(author) + " " + str(pull_request))
	tx.run("MERGE (a:Developer {id:$devID}) MERGE (b:PullRequest {id:$prID}) MERGE (a)-[:proposes]->(b)",
		   devID=author,
		   prID=pull_request)


def add_includes_relation(tx, commit, file_name):
	print("Adding includes relation: " + str(commit) + " " + str(file_name))
	tx.run("MERGE (a:Commit {id:$commitID}) MERGE (b:File {id:$fileName}) MERGE (a)-[:includes]->(b)",
		   commitID=commit,
		   fileName=file_name)


def add_pr_includes_relation(tx, pr_number, file_name):
	print("Adding pr_includes relation: " + str(pr_number) + " " + str(file_name))
	tx.run("MERGE (a:PullRequest {id:$prID}) MERGE (b:File {id:$fileName}) MERGE (a)-[:includes]->(b)",
		   prID=pr_number,
		   fileName=file_name)


# Fetch all issues/pull requests from GitHub
repo = GitHub(owner=GITHUB_REPO_OWNER, repository=GITHUB_REPO_NAME, api_token=GITHUB_API_TOKEN)
for item in repo.fetch():
	number = item['data']['number']
	author = item['data']['user']['login']
	if 'pull_request' in item['data']:
		session.write_transaction(add_proposes_relation, number, author)

		# Get files in the pr. Perceval doesn't support so send a request to GitHub API
		# https://developer.github.com/v3/pulls/#list-pull-requests-files
		prFilesUrl = GITHUB_API_URL + "/repos/%s/%s/pulls/%s/files" % (GITHUB_REPO_OWNER, GITHUB_REPO_NAME, number)
		headers = {'Authorization': 'token ' + GITHUB_API_TOKEN}
		r = requests.get(prFilesUrl, headers=headers)
		filesInPr = r.json()
		for file in filesInPr:
			session.write_transaction(add_pr_includes_relation, number, file['filename'])

	else:
		session.write_transaction(add_opens_relation, number, author)

# Directory for letting Perceval clone the git
repo_dir = '/tmp/perceval-test.git'
shutil.rmtree(repo_dir, ignore_errors=True)  # CAUTION If repo_dir == '/', it could delete all your disk files.
# Fetch all commits from Git
repo = Git(uri=GITHUB_REPO_URL, gitpath=repo_dir)
for commit in repo.fetch():
	data = commit['data']
	commitID = data['commit']
	# Perceval does not parse GitHub username, so get it manually
	commitUrl = GITHUB_API_URL + "/repos/%s/%s/commits/%s" % (GITHUB_REPO_OWNER, GITHUB_REPO_NAME, commitID)

	headers = {'Authorization': 'token ' + GITHUB_API_TOKEN}
	r = requests.get(commitUrl, headers=headers)

	commit_json = r.json()
	author = None
	if 'author' in commit_json and commit_json['author']:
		author = commit_json['author']['login']
	else:
		print("WARNING: " + str(commitID) + " does NOT have an author")

	if author:
		session.write_transaction(add_commits_relation, commitID, author)

	# Add files in the commit
	files = data['files']
	for file in files:
		fileName = file['file']
		session.write_transaction(add_includes_relation, commitID, fileName)
