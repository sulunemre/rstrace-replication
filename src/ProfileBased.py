import collections


def recommendReviewers(profiles, commit):
    recommendationScores = {}  # {Reviewer name: score}
    commitMultiset = getMultisetFromCommit(commit)

    for reviewerName, reviewerProfile in profiles.items():
        similarity = tverskyIndexForMultisets(
            reviewerProfile, commitMultiset, 1, 0)  # α = 0 and β = 1
        recommendationScores[reviewerName] = similarity

    # Sort by score and return only names
    if len(recommendationScores) != 0:
        recommendationScores = {k: v for k, v in sorted(recommendationScores.items(), key=lambda item: item[1], reverse=True)}
    recommendedReviewers = [*recommendationScores]
    
    return recommendedReviewers


def getMultisetFromCommit(commit):
    """Converts the file paths of a commit to multiset

    Arguments:
        commit {dict} -- Commit must have modifiedFileNames key

    Returns:
        Counter -- example: (java : 5), (main : 3), (package1 : 2), (src : 5)
    """
    multiset = collections.Counter()
    for filePath in commit['modifiedFileNames']:
        for token in filePath.split('/'):
            multiset[token] += 1

    return multiset


def tverskyIndexForMultisets(multiset1, multiset2, alpha, beta):
    """T(X, Y ) = |X ∩ Y | / (|X ∪ Y | − α|X − Y | − β|Y − X|)
    """
    numerator = sum((multiset1 & multiset2).values())
    denominator = sum((multiset1 | multiset2).values()) - alpha * sum(
        (multiset1 - multiset2).values()) - beta * sum((multiset2 - multiset1).values())
    return numerator / denominator
