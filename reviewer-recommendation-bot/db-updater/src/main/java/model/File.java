package model;

/**
 * Check https://developer.github.com/v3/pulls/#list-pull-requests-files
 */
public class File {
	private String sha;
	private String filename;
	private String status;
	private long additions;
	private long deletions;
	private long changes;
	private String blob_url;
	private String raw_url;
	private String contents_url;
	private String patch;

	public String getFileName() {
		return filename;
	}
}
