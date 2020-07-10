import model.Commit;
import org.json.JSONArray;
import org.json.JSONObject;
import org.neo4j.driver.v1.AuthTokens;
import org.neo4j.driver.v1.Driver;
import org.neo4j.driver.v1.GraphDatabase;
import org.neo4j.driver.v1.Session;

import java.util.LinkedList;
import java.util.List;

class DatabaseConnection {
	private Driver driver;
	private Session session;

	DatabaseConnection(String host, String username, String password) {
		driver = GraphDatabase.driver(host, AuthTokens.basic(username, password));
		session = driver.session();
		System.out.println("Database connection started.");
	}

	void addPushToDB(String json) {
		JSONArray commits = new JSONObject(json).getJSONArray("commits");

		for (Object o : commits) {
			JSONObject commit = (JSONObject) o;
			String commitID = commit.getString("id");
			String author = commit.getJSONObject("author").getString("username");
			List<String> fileNames = new LinkedList();
			for (Object obj : commit.getJSONArray("added")) {
				fileNames.add((String) obj);
			}
			for (Object obj : commit.getJSONArray("removed")) {
				fileNames.add((String) obj);
			}
			for (Object obj : commit.getJSONArray("modified")) {
				fileNames.add((String) obj);
			}
			Commit newCommit = new Commit(commitID, author, fileNames);

			addCommitToDB(newCommit);
		}
	}

	private void addCommitToDB(Commit newCommit) {
		String addCommitDeveloperRelationQuery = "MERGE (b:Commit{id:\"" + newCommit.getId() + "\"})" + "MERGE (a:Developer{id:\"" + newCommit.getAuthorUsername() + "\"})"
				+ "MERGE (a)-[:commits]->(b)";
		session.run(addCommitDeveloperRelationQuery);

		for (String fileName : newCommit.getFileNames()) {
			String addCommitFileRelationQuery = "MERGE (b:Commit{id:\"" + newCommit.getId() + "\"})"
					+ "MERGE (a:File{id:\"" + fileName + "\"})"
					+ "MERGE (b)-[:includes]->(a)";

			session.run(addCommitFileRelationQuery);
		}
	}

	void addIssueToDB(String json) {
		// TODO: Under construction
	}

	void addPrToDB(String json) {
		// TODO: Under construction
	}

	void close() {
		session.close();
		driver.close();
	}
}
