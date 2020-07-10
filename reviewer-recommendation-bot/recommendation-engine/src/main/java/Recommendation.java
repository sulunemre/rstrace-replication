import model.PullRequest;
import org.neo4j.driver.v1.Record;
import org.neo4j.driver.v1.Session;
import org.neo4j.driver.v1.StatementResult;
import org.neo4j.driver.v1.exceptions.ClientException;

import java.util.*;

class Recommendation {
	private PullRequest inputPR;
	private List<String> recommendedReviewers;
	private Session session;

	Recommendation(PullRequest inputPR, Session session) {
		this.inputPR = inputPR;
		this.session = session;
	}

	List<String> getRecommendedReviewers() {
		return recommendedReviewers;
	}

	void recommend() {
		if (inputPR == null || session == null) {
			throw new NullPointerException("Recommendation parameters cannot be null");
		} else {
			// Find appropriate reviewer
			List<String> modifiedFileNames = inputPR.getModifiedFileNames();
			Map<String, Double> recommendedReviewers = new HashMap(); // Developer name and sum of know about scores
			Map<String, Object> params = new HashMap();
			params.put("fileNames", modifiedFileNames);

			String recommendationQuery = "MATCH (a:Developer)-[r*]->(b:File) WHERE b.id IN {fileNames} RETURN a.id, LENGTH(r), b.id, SUM(1.0/LENGTH(r)) AS KnowAboutScore ORDER BY a.id";
			StatementResult response2 = session.run(recommendationQuery, params); // Params still valid here
			try {
				while (response2.hasNext()) {
					Record record = response2.next();
					String developerName = record.get("a.id", "");
					double knowAbout = record.get("KnowAboutScore").asDouble();
					recommendedReviewers.merge(developerName, knowAbout, Double::sum); // https://stackoverflow.com/a/42648785
				}
			} catch (ClientException e) {
//				System.out.println("EXCEPTION: Invalid query in commit " + commitId);
				///TODO: approprate error message
			}

			Map<String, Double> scoresSorted = sortByValue(recommendedReviewers);

			// Compare recommendation
			List<String> recommendedReviewersList = new ArrayList(); // Sorted list of reviewers' names
			recommendedReviewersList.addAll(scoresSorted.keySet()); // Fill the list

			inputPR.setRecommendedReviewers(recommendedReviewersList);
			this.recommendedReviewers = recommendedReviewersList;
		}
	}

	/**
	 * https://stackoverflow.com/a/2581754
	 *
	 * @param <K>
	 * @param <V>
	 * @param map
	 * @return
	 */
	private static <K, V extends Comparable<? super V>> Map<K, V> sortByValue(Map<K, V> map) {
		List<Map.Entry<K, V>> list = new ArrayList<>(map.entrySet());
		list.sort((Collections.reverseOrder(Map.Entry.comparingByValue())));

		Map<K, V> result = new LinkedHashMap<>();
		for (Map.Entry<K, V> entry : list) {
			result.put(entry.getKey(), entry.getValue());
		}

		return result;
	}
}
