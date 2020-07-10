import fi.iki.elonen.NanoHTTPD;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

public class WebServer extends NanoHTTPD {
	final static private int PORT = 8081;

	WebServer() throws IOException {
		super(PORT);
		start(NanoHTTPD.SOCKET_READ_TIMEOUT, false);
		System.out.println("Web server is running on port " + PORT);
	}

	public Response serve(IHTTPSession session) {
		System.out.println("New request arrived.");

		final Map<String, String> map = new HashMap();
		final String JSON;
		try {
			session.parseBody(map);
			JSON = map.get("postData");
		} catch (IOException | ResponseException e) {
			System.out.println("ERROR: Request is not proper");
			return null;
		}

		String action = session.getUri();
		Method method = session.getMethod();

		if (action.equals("/issue") && method == Method.POST) {
			Main.handleIssue(JSON);
		} else if (action.equals("/pr") && method == Method.POST) {
			Main.handlePr(JSON);
		} else if (action.equals("/push") && method == Method.POST) {
			Main.handlePush(JSON);
		}

		return newFixedLengthResponse(Response.Status.OK, "text/plain", "OK");
	}
}