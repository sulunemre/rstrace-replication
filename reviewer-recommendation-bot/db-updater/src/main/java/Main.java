import java.io.IOException;

public class Main {
	private static final String DB_ADDRESS = "bolt://graph-db:7687";
	private static final String DB_USERNAME = "neo4j";
	private static final String DB_PASSWORD = "rstrace";

	public static void main(String[] args) throws IOException {
		// Run web server and listen requests
		new WebServer();
	}

	static void handlePush(String json) {
		DatabaseConnection dc = new DatabaseConnection(DB_ADDRESS, DB_USERNAME, DB_PASSWORD);
		dc.addPushToDB(json);
		dc.close();
	}

	static void handleIssue(String json) {
		DatabaseConnection dc = new DatabaseConnection(DB_ADDRESS, DB_USERNAME, DB_PASSWORD);
		dc.addIssueToDB(json);
		dc.close();
	}

	public static void handlePr(String json) {
		DatabaseConnection dc = new DatabaseConnection(DB_ADDRESS, DB_USERNAME, DB_PASSWORD);
		dc.addPrToDB(json);
		dc.close();
	}
}
