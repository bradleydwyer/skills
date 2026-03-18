#!/usr/bin/env python3
"""YouTube Data API v3 CLI for Claude Code.

Usage:
    python3 yt.py search "query" [options]
    python3 yt.py video VIDEO_ID_OR_URL [options]
    python3 yt.py channel [options]
    python3 yt.py comments VIDEO_ID_OR_URL [options]
    python3 yt.py playlist PLAYLIST_ID_OR_URL [options]
    python3 yt.py captions VIDEO_ID_OR_URL
    python3 yt.py transcript VIDEO_ID_OR_URL [--lang LANG]

No pip dependencies — uses only Python stdlib + yt-dlp (for transcripts).
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://www.googleapis.com/youtube/v3"


# --- Auth ---

def get_api_key():
    """Get API key from env var or config file."""
    key = os.environ.get("YOUTUBE_API_KEY")
    if key:
        return key.strip()
    config_path = os.path.expanduser("~/.config/youtube-api-key")
    if os.path.exists(config_path):
        with open(config_path) as f:
            return f.read().strip()
    print(
        "Error: No YouTube API key found.\n"
        "Set YOUTUBE_API_KEY env var or save your key to ~/.config/youtube-api-key",
        file=sys.stderr,
    )
    sys.exit(1)


def get_oauth_token():
    """Get OAuth access token if available."""
    token_path = os.path.expanduser("~/.config/youtube-oauth.json")
    if not os.path.exists(token_path):
        return None
    with open(token_path) as f:
        data = json.load(f)
    # Check if token needs refresh
    if "refresh_token" in data and "expires_in" in data:
        # For simplicity, always try the access token first — the caller
        # should handle 401 and refresh if needed
        pass
    return data.get("access_token")


def refresh_oauth_token():
    """Refresh the OAuth access token using the refresh token."""
    token_path = os.path.expanduser("~/.config/youtube-oauth.json")
    client_path = os.path.expanduser("~/.config/youtube-oauth-client.json")
    if not os.path.exists(token_path) or not os.path.exists(client_path):
        return None

    with open(token_path) as f:
        tokens = json.load(f)
    with open(client_path) as f:
        client = json.load(f)

    installed = client.get("installed", client.get("web", {}))
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        return None

    data = urllib.parse.urlencode({
        "client_id": installed["client_id"],
        "client_secret": installed["client_secret"],
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }).encode()

    try:
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
        with urllib.request.urlopen(req) as resp:
            new_tokens = json.loads(resp.read().decode())
        # Preserve refresh token (not always returned on refresh)
        new_tokens.setdefault("refresh_token", refresh_token)
        with open(token_path, "w") as f:
            json.dump(new_tokens, f, indent=2)
        return new_tokens.get("access_token")
    except urllib.error.HTTPError:
        return None


# --- API ---

def api_request(endpoint, params, use_oauth=False):
    """Make a request to the YouTube Data API v3."""
    if use_oauth:
        token = get_oauth_token()
        if not token:
            print(
                "OAuth required but no token found. Run oauth_setup.py first.",
                file=sys.stderr,
            )
            sys.exit(1)
        url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    else:
        params["key"] = get_api_key()
        url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        # If OAuth 401, try refreshing
        if use_oauth and e.code == 401:
            new_token = refresh_oauth_token()
            if new_token:
                req = urllib.request.Request(
                    url, headers={"Authorization": f"Bearer {new_token}"}
                )
                with urllib.request.urlopen(req) as resp:
                    return json.loads(resp.read().decode())

        error_body = e.read().decode()
        try:
            err = json.loads(error_body)
            msg = err.get("error", {}).get("message", error_body)
        except json.JSONDecodeError:
            msg = error_body
        print(f"API Error {e.code}: {msg}", file=sys.stderr)
        sys.exit(1)


# --- URL Parsing ---

def extract_video_id(value):
    """Extract video ID from a URL or return as-is if already an ID."""
    patterns = [
        r"(?:youtube\.com/watch\?.*v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)
    # Looks like a bare ID
    if re.match(r"^[a-zA-Z0-9_-]{11}$", value):
        return value
    return value


def extract_playlist_id(value):
    """Extract playlist ID from a URL or return as-is."""
    match = re.search(r"[?&]list=([a-zA-Z0-9_-]+)", value)
    return match.group(1) if match else value


def extract_channel_id(value):
    """Extract channel ID from a URL or return as-is."""
    match = re.search(r"youtube\.com/channel/([a-zA-Z0-9_-]+)", value)
    return match.group(1) if match else value


# --- Commands ---

def cmd_search(args):
    """Search for videos, channels, or playlists."""
    params = {
        "part": "snippet",
        "q": args.query,
        "maxResults": min(args.max_results, 50),
        "type": args.type,
    }
    if args.channel_id:
        params["channelId"] = args.channel_id
    if args.order:
        params["order"] = args.order
    if args.published_after:
        params["publishedAfter"] = args.published_after
    if args.published_before:
        params["publishedBefore"] = args.published_before
    if args.page_token:
        params["pageToken"] = args.page_token

    result = api_request("search", params)
    print(json.dumps(result, indent=2))


def cmd_video(args):
    """Get video details."""
    video_ids = ",".join(extract_video_id(v.strip()) for v in args.video_id.split(","))
    parts = args.parts or "snippet,statistics,contentDetails"
    params = {"part": parts, "id": video_ids}
    result = api_request("videos", params)
    print(json.dumps(result, indent=2))


def cmd_channel(args):
    """Get channel info or list uploads."""
    if args.list_uploads:
        channel_id = args.channel_id
        if not channel_id and args.handle:
            ch = api_request("channels", {"part": "id", "forHandle": args.handle})
            if not ch.get("items"):
                print(f"Channel not found for handle: {args.handle}", file=sys.stderr)
                sys.exit(1)
            channel_id = ch["items"][0]["id"]

        if not channel_id:
            print("Provide --channel-id or --handle with --list-uploads", file=sys.stderr)
            sys.exit(1)

        ch = api_request("channels", {"part": "contentDetails", "id": channel_id})
        if not ch.get("items"):
            print("Channel not found", file=sys.stderr)
            sys.exit(1)
        uploads_id = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        params = {
            "part": "snippet",
            "playlistId": uploads_id,
            "maxResults": min(args.max_results, 50),
        }
        if args.page_token:
            params["pageToken"] = args.page_token
        result = api_request("playlistItems", params)
        print(json.dumps(result, indent=2))
    else:
        parts = args.parts or "snippet,statistics,brandingSettings"
        params = {"part": parts}
        if args.channel_id:
            params["id"] = extract_channel_id(args.channel_id)
        elif args.username:
            params["forUsername"] = args.username
        elif args.handle:
            params["forHandle"] = args.handle
        else:
            print("Provide --channel-id, --username, or --handle", file=sys.stderr)
            sys.exit(1)
        result = api_request("channels", params)
        print(json.dumps(result, indent=2))


def cmd_comments(args):
    """Get video comments."""
    video_id = extract_video_id(args.video_id)
    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": min(args.max_results, 100),
        "order": args.order,
    }
    if args.page_token:
        params["pageToken"] = args.page_token
    if args.search:
        params["searchTerms"] = args.search
    result = api_request("commentThreads", params)
    print(json.dumps(result, indent=2))


def cmd_playlist(args):
    """Get playlist items."""
    playlist_id = extract_playlist_id(args.playlist_id)
    params = {
        "part": "snippet,contentDetails",
        "playlistId": playlist_id,
        "maxResults": min(args.max_results, 50),
    }
    if args.page_token:
        params["pageToken"] = args.page_token
    result = api_request("playlistItems", params)
    print(json.dumps(result, indent=2))


def cmd_captions(args):
    """List available caption tracks."""
    video_id = extract_video_id(args.video_id)
    params = {"part": "snippet", "videoId": video_id}
    result = api_request("captions", params)
    print(json.dumps(result, indent=2))


def cmd_transcript(args):
    """Get transcript text using yt-dlp."""
    video_id = extract_video_id(args.video_id)
    url = f"https://www.youtube.com/watch?v={video_id}"
    lang = args.lang or "en"

    with tempfile.TemporaryDirectory() as tmpdir:
        out_template = os.path.join(tmpdir, "sub")
        cmd = [
            "yt-dlp",
            "--write-sub",
            "--write-auto-sub",
            "--sub-lang", lang,
            "--sub-format", "vtt",
            "--skip-download",
            "-o", out_template,
            url,
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except FileNotFoundError:
            print(
                "Error: yt-dlp not found. Install with: brew install yt-dlp",
                file=sys.stderr,
            )
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"yt-dlp error: {e.stderr}", file=sys.stderr)
            sys.exit(1)

        # Find the subtitle file
        vtt_file = None
        for f in os.listdir(tmpdir):
            if f.endswith(".vtt"):
                vtt_file = os.path.join(tmpdir, f)
                break

        if not vtt_file:
            print("No subtitles found for this video", file=sys.stderr)
            sys.exit(1)

        # Parse VTT and extract clean text
        with open(vtt_file) as f:
            content = f.read()

        lines = []
        seen = set()
        for line in content.split("\n"):
            line = line.strip()
            # Skip VTT headers and timestamps
            if (
                not line
                or line.startswith("WEBVTT")
                or line.startswith("Kind:")
                or line.startswith("Language:")
                or line.startswith("NOTE")
                or "-->" in line
                or re.match(r"^\d+$", line)
            ):
                continue
            # Strip VTT formatting tags
            clean = re.sub(r"<[^>]+>", "", line)
            if clean and clean not in seen:
                seen.add(clean)
                lines.append(clean)

        print("\n".join(lines))


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description="YouTube Data API v3 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # search
    p = subparsers.add_parser("search", help="Search YouTube")
    p.add_argument("query")
    p.add_argument("--max-results", type=int, default=10)
    p.add_argument("--type", default="video", choices=["video", "channel", "playlist"])
    p.add_argument("--channel-id", help="Limit search to a channel")
    p.add_argument(
        "--order",
        default="relevance",
        choices=["relevance", "date", "rating", "viewCount", "title"],
    )
    p.add_argument("--published-after", help="ISO 8601 (e.g. 2024-01-01T00:00:00Z)")
    p.add_argument("--published-before", help="ISO 8601 datetime")
    p.add_argument("--page-token", help="Pagination token")
    p.set_defaults(func=cmd_search)

    # video
    p = subparsers.add_parser("video", help="Get video details")
    p.add_argument("video_id", help="Video ID, URL, or comma-separated IDs")
    p.add_argument("--parts", help="Default: snippet,statistics,contentDetails")
    p.set_defaults(func=cmd_video)

    # channel
    p = subparsers.add_parser("channel", help="Get channel info or uploads")
    p.add_argument("--channel-id", help="Channel ID")
    p.add_argument("--username", help="Channel username")
    p.add_argument("--handle", help="Channel handle (e.g. @mkbhd)")
    p.add_argument("--list-uploads", action="store_true", help="List recent uploads")
    p.add_argument("--max-results", type=int, default=10)
    p.add_argument("--parts", help="API parts to request")
    p.add_argument("--page-token", help="Pagination token")
    p.set_defaults(func=cmd_channel)

    # comments
    p = subparsers.add_parser("comments", help="Get video comments")
    p.add_argument("video_id", help="Video ID or URL")
    p.add_argument("--max-results", type=int, default=20)
    p.add_argument("--order", default="relevance", choices=["relevance", "time"])
    p.add_argument("--search", help="Filter comments containing this term")
    p.add_argument("--page-token", help="Pagination token")
    p.set_defaults(func=cmd_comments)

    # playlist
    p = subparsers.add_parser("playlist", help="Get playlist items")
    p.add_argument("playlist_id", help="Playlist ID or URL")
    p.add_argument("--max-results", type=int, default=25)
    p.add_argument("--page-token", help="Pagination token")
    p.set_defaults(func=cmd_playlist)

    # captions
    p = subparsers.add_parser("captions", help="List available caption tracks")
    p.add_argument("video_id", help="Video ID or URL")
    p.set_defaults(func=cmd_captions)

    # transcript
    p = subparsers.add_parser("transcript", help="Get transcript text (uses yt-dlp)")
    p.add_argument("video_id", help="Video ID or URL")
    p.add_argument("--lang", default="en", help="Language code (default: en)")
    p.set_defaults(func=cmd_transcript)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
