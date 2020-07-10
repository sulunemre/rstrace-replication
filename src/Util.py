def parseCommitMessage(message):
    relatedIssues = []
    reviewers = []
    
    lines = message.split("\n")
    for line in lines:
        if line.startswith("Task-number:") or line.startswith("Task-Id:") or line.startswith("Task-id:"):
            relatedIssues.append(line.split(":")[1].strip())
        elif (line.startswith("Reviewed-by:")):
            nameWithEmail = line.split(":")[1].strip()
            nameWithoutEmail = nameWithEmail.split("<")[0].strip()
            reviewers.append(nameWithoutEmail)

    return relatedIssues, reviewers