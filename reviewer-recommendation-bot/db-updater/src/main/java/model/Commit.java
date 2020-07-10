package model;

import java.util.List;

public class Commit {
	private String id;
	private String authorUsername;
	private List<String> fileNames;

	public Commit(String id, String authorUsername, List<String> files) {
		this.id = id;
		this.authorUsername = authorUsername;
		this.fileNames = files;
	}

	public String getId() {
		return id;
	}

	public String getAuthorUsername() {
		return authorUsername;
	}

	public List<String> getFileNames() {
		return fileNames;
	}
}
