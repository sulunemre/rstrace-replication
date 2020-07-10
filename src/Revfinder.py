from RevFinderStringCompare import *
import concurrent.futures


def recommendReviewers(pastCommits, newCommit):
    """Runs four different methods in parallel and combines their results

    Arguments:
        pastCommits {[type]} -- [description]
        newCommit {[type]} -- [description]

    Returns:
        [type] -- [description]
    """
    # Run in different processes
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        future1 = executor.submit(
            recommendReviewersByMethod, pastCommits, newCommit, 'LCP')
        future2 = executor.submit(
            recommendReviewersByMethod, pastCommits, newCommit, 'LCSuff')
        future3 = executor.submit(
            recommendReviewersByMethod, pastCommits, newCommit, 'LCSubstr')
        future4 = executor.submit(
            recommendReviewersByMethod, pastCommits, newCommit, 'LCSubseq')

        l1 = future1.result()
        l2 = future2.result()
        l3 = future3.result()
        l4 = future4.result()

    # Combination
    reviewerScores = {}

    for i, reviewer in enumerate(l1):
        score = len(l1) - i
        if reviewer in reviewerScores:
            reviewerScores[reviewer] += score
        else:
            reviewerScores[reviewer] = score

    for i, reviewer in enumerate(l2):
        score = len(l2) - i
        if reviewer in reviewerScores:
            reviewerScores[reviewer] += score
        else:
            reviewerScores[reviewer] = score

    for i, reviewer in enumerate(l3):
        score = len(l3) - i
        if reviewer in reviewerScores:
            reviewerScores[reviewer] += score
        else:
            reviewerScores[reviewer] = score

    for i, reviewer in enumerate(l4):
        score = len(l4) - i
        if reviewer in reviewerScores:
            reviewerScores[reviewer] += len(l4) - i
        else:
            reviewerScores[reviewer] = len(l4) - i

    # Sort by score and return only names
    if len(reviewerScores) != 0:
        {k: v for k, v in sorted(
            reviewerScores.items(), key=lambda item: item[1], reverse=True)}

    final_list = [*reviewerScores]

    return final_list


def recommendReviewersByMethod(pastCommits, newCommit, method):
    recommendedReviewers = {}  # dicts {reviewerName: score}
    for pastCommit in pastCommits:
        newCommitFiles = newCommit["modifiedFileNames"]
        pastCommitFiles = pastCommit["modifiedFileNames"]

        # Compute review similarity score between newCommit and pastCommit
        score = 0
        for newFile in newCommitFiles:
            for pastFile in pastCommitFiles:
                score += filePathSimilarity(newFile, pastFile, method)
        score = score / (len(newCommitFiles) * len(pastCommitFiles))

        # Propagate review similarity scores to code-reviewers who involved in a previous review Rp
        if score > 0:
            for reviewer in pastCommit["reviewers"]:
                if reviewer in recommendedReviewers:
                    recommendedReviewers[reviewer] += score
                else:
                    recommendedReviewers[reviewer] = score

    # Sort by score and return only names
    if len(recommendedReviewers) != 0:
        {k: v for k, v in sorted(
            recommendedReviewers.items(), key=lambda item: item[1], reverse=True)}

    return [*recommendedReviewers]


def filePathSimilarity(newFile, pastFile, method):
    score = -1
    if method == 'LCP':
        score = LCP(newFile, pastFile)
    elif method == 'LCSuff':
        score = LCSuff(newFile, pastFile)
    elif method == 'LCSubstr':
        score = LCSubstr(newFile, pastFile)
    elif method == 'LCSubseq':
        score = LCSubseq(newFile, pastFile)
    else:
        raise ValueError(
            f"{method} is not valid. Method can be: LCP, LCSuff, LCSubstr, LCSubseq")

    return score
