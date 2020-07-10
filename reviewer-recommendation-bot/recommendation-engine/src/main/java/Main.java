import model.PullRequest;
import org.neo4j.driver.v1.AuthTokens;
import org.neo4j.driver.v1.Driver;
import org.neo4j.driver.v1.GraphDatabase;
import org.neo4j.driver.v1.Session;

import java.io.IOException;

public class Main {
	private static final String DB_ADDRESS = "bolt://graph-db:7687";
	private static final String DB_USERNAME= "neo4j";
	private static final String DB_PASSWORD = "rstrace";
	private static Session session;

	public static void main(String[] args) throws IOException {
		// Connect to DB
		Driver driver = GraphDatabase.driver(DB_ADDRESS, AuthTokens.basic(DB_USERNAME, DB_PASSWORD));
		session = driver.session();

		// Run web server and listen requests
		new WebServer();
	}

	static void handlePullRequest(PullRequest pullRequest){
		Recommendation recommendation = new Recommendation(pullRequest, session);
		recommendation.recommend();
		System.out.println(recommendation.getRecommendedReviewers());
	}
}
