#!/usr/bin/env python3
"""OAuth 2.0 setup for YouTube Data API v3.

Required only for downloading caption tracks you own.
Most operations work fine with just an API key.

Setup:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create an OAuth 2.0 Client ID (type: Desktop app)
3. Download the JSON and save as ~/.config/youtube-oauth-client.json
4. Run this script
"""

import http.server
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

CLIENT_CONFIG_PATH = os.path.expanduser("~/.config/youtube-oauth-client.json")
TOKEN_PATH = os.path.expanduser("~/.config/youtube-oauth.json")
SCOPES = "https://www.googleapis.com/auth/youtube.force-ssl"
REDIRECT_PORT = 8789
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"


def load_client_config():
    if not os.path.exists(CLIENT_CONFIG_PATH):
        print(f"Client config not found at {CLIENT_CONFIG_PATH}")
        print()
        print("To set up OAuth:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create an OAuth 2.0 Client ID (type: Desktop app)")
        print(f"3. Download the JSON and save as {CLIENT_CONFIG_PATH}")
        print("4. Run this script again")
        sys.exit(1)

    with open(CLIENT_CONFIG_PATH) as f:
        data = json.load(f)

    installed = data.get("installed", data.get("web", {}))
    return installed["client_id"], installed["client_secret"]


def exchange_code(client_id, client_secret, code):
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def main():
    client_id, client_secret = load_client_config()

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode({
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPES,
            "access_type": "offline",
            "prompt": "consent",
        })
    )

    print("Opening browser for authorization...")
    webbrowser.open(auth_url)

    # Local server to capture the OAuth callback
    auth_code = None

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_code
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)

            error = params.get("error", [None])[0]
            if error:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f"<h1>Authorization failed: {error}</h1>".encode())
                return

            auth_code = params.get("code", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<h1>Authorization complete!</h1>"
                b"<p>You can close this tab and return to your terminal.</p>"
            )

        def log_message(self, format, *args):
            pass  # Suppress request logging

    server = http.server.HTTPServer(("localhost", REDIRECT_PORT), Handler)
    print(f"Waiting for authorization on localhost:{REDIRECT_PORT}...")
    server.handle_request()

    if not auth_code:
        print("Authorization failed — no code received.", file=sys.stderr)
        sys.exit(1)

    print("Exchanging code for tokens...")
    try:
        tokens = exchange_code(client_id, client_secret, auth_code)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Token exchange failed: {error_body}", file=sys.stderr)
        sys.exit(1)

    with open(TOKEN_PATH, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(TOKEN_PATH, 0o600)

    print(f"Tokens saved to {TOKEN_PATH}")
    print("OAuth setup complete!")


if __name__ == "__main__":
    main()
