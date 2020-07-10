package model;

import java.util.LinkedList;
import java.util.List;

public class PullRequest {
	private List<File> modifiedFiles;
	private List<String> recommendedReviewers;

	public PullRequest(List<File> modifiedFiles) {
		this.modifiedFiles = modifiedFiles;
	}

	public List<File> getModifiedFiles() {
		return modifiedFiles;
	}

	public List<String> getModifiedFileNames() {
		List<String> modifiedFileNames = new LinkedList();
		for (File file : modifiedFiles) {
			modifiedFileNames.add(file.getFileName());
		}
		return modifiedFileNames;
	}

	public void setModifiedFiles(List<File> modifiedFiles) {
		this.modifiedFiles = modifiedFiles;
	}

	public List<String> getRecommendedReviewers() {
		return recommendedReviewers;
	}

	public void setRecommendedReviewers(List<String> recommendedReviewers) {
		this.recommendedReviewers = recommendedReviewers;
	}

	@Override
	public String toString() {
		return "model.PullRequest{" +
				"modifiedFiles=" + modifiedFiles +
				'}';
	}
}
