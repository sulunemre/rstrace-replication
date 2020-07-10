import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import fi.iki.elonen.NanoHTTPD;
import model.File;
import model.PullRequest;

import java.io.IOException;
import java.lang.reflect.Type;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class WebServer extends NanoHTTPD {

	WebServer() throws IOException {
		super(8080);
		start(NanoHTTPD.SOCKET_READ_TIMEOUT, false);
		System.out.println("Web server is running on port 8080.");
	}

	public Response serve(IHTTPSession session) {
		System.out.println("New request arrived.");

		// Parse request body https://stackoverflow.com/a/27529084
		final Map<String, String> map = new HashMap();
		try {
			session.parseBody(map);
		} catch (IOException | ResponseException e) {
			e.printStackTrace();
		}

		// Parse json
		final String JSON = map.get("postData");
		System.out.println("Raw JSON: " + JSON);
		Type listType = new TypeToken<List<File>>() {
		}.getType(); // https://stackoverflow.com/a/18547661
		List<File> modifiedFiles = new Gson().fromJson(JSON, listType);

		// Create pull request and handle it
		PullRequest pullRequest = new PullRequest(modifiedFiles);
		Main.handlePullRequest(pullRequest);

		// Send response
		String responseJSON = new Gson().toJson(pullRequest.getRecommendedReviewers());
		return newFixedLengthResponse(responseJSON);
	}
}