import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from ytmusicapi import YTMusic

app = Flask(__name__)
CORS(app)

# ✅ Initialize YTMusic
try:
    print("⚙️ Initializing YTMusic...")
    ytmusic = YTMusic(language='en', location='IN')
    print("✅ YTMusic initialized")
except Exception as e:
    print(f"❌ YTMusic init failed: {e}")
    ytmusic = None

# ✅ Root route
@app.route("/")
def index():
    return jsonify({"status": "✅ music-backend is running"}), 200

# ✅ Favicon route (empty 204)
@app.route("/favicon.ico")
def favicon():
    return '', 204

# 🔍 Search songs
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q")
    print(f"[SEARCH] Searching for: {query}")

    if not query:
        return jsonify({"error": "Missing search query"}), 400

    try:
        results = ytmusic.search(query, filter="songs")
        return jsonify(results)
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        return jsonify({"error": str(e)}), 500

# 🎵 Get song metadata
@app.route("/metadata", methods=["GET"])
def fetch_metadata():
    video_id = request.args.get("q")
    print(f"[METADATA] Fetching for video ID: {video_id}")

    if not video_id:
        return jsonify({'error': 'Missing video ID'}), 400

    try:
        result = ytmusic.get_song(video_id)
        return jsonify(result)
    except Exception as e:
        print(f"[ERROR] Metadata fetch failed: {e}")
        return jsonify({'error': str(e)}), 500

# 🔥 Trending charts
@app.route("/trending", methods=["GET"])
def trending():
    print("[TRENDING] Fetching charts")
    try:
        charts = ytmusic.get_charts()
        return jsonify(charts)
    except Exception as e:
        print(f"[ERROR] Trending fetch failed: {e}")
        return jsonify({"error": str(e)}), 500

# 📃 Playlist details
@app.route("/playlist", methods=["GET"])
def get_playlist():
    playlist_id = request.args.get("id")
    print(f"[PLAYLIST] Fetching: {playlist_id}")

    if not playlist_id:
        return jsonify({"error": "Missing playlist ID"}), 400

    try:
        playlist = ytmusic.get_playlist(playlist_id)
        return jsonify(playlist)
    except Exception as e:
        print(f"[ERROR] Playlist fetch failed: {e}")
        return jsonify({"error": str(e)}), 500

# 💿 Album details
@app.route("/album", methods=["GET"])
def get_album():
    album_id = request.args.get("id")
    print(f"[ALBUM] Fetching: {album_id}")

    if not album_id:
        return jsonify({"error": "Missing album ID"}), 400

    try:
        album = ytmusic.get_album(album_id)
        return jsonify(album)
    except Exception as e:
        print(f"[ERROR] Album fetch failed: {e}")
        return jsonify({"error": str(e)}), 500

# 👤 Artist details
@app.route("/artist", methods=["GET"])
def get_artist():
    artist_id = request.args.get("id")
    print(f"[ARTIST] Fetching: {artist_id}")

    if not artist_id:
        return jsonify({"error": "Missing artist ID"}), 400

    try:
        artist = ytmusic.get_artist(artist_id)
        return jsonify(artist)
    except Exception as e:
        print(f"[ERROR] Artist fetch failed: {e}")
        return jsonify({"error": str(e)}), 500

# 🌐 Catch-all fallback
@app.route("/<path:path>")
def catch_all(path):
    return jsonify({"catch": path}), 200

# 🛠️ Run the server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"👟 Starting development server on port {port}")
    app.run(host="0.0.0.0", port=port)
