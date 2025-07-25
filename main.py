import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from yt.stream import get_stream_url_with_proxy_rotation
from yt.metadata import get_metadata
from proxies.proxy_manager import ProxyManager
from ytmusicapi import YTMusic

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables
proxy_manager = ProxyManager()
stream_cache = {}  # { video_id: { "url": ..., "timestamp": ... } }
CACHE_TTL_SECONDS = 3600  # 1 hour

# Initialize YTMusic
try:
    print("⚙️ Initializing YTMusic...")
    ytmusic = YTMusic()
    print("✅ YTMusic initialized")
except Exception as e:
    print(f"❌ YTMusic init failed: {e}")
    ytmusic = None

# Root route
@app.route("/")
def index():
    return jsonify({"status": "✅ music-backend is running"}), 200

# Favicon route (no icon response)
@app.route("/favicon.ico")
def favicon():
    return '', 204

# Catch-all for unknown routes
@app.route("/<path:path>")
def catch_all(path):
    return jsonify({"catch": path}), 200

# Route: /stream?video_id=xyz
@app.route("/stream", methods=["GET"])
def stream():
    video_id = request.args.get("video_id")
    print(f"[DEBUG] video_id received: {video_id}")

    if not video_id:
        return jsonify({"error": "Missing video ID"}), 400

    # Check cache
    cached = stream_cache.get(video_id)
    if cached:
        age = time.time() - cached["timestamp"]
        if age < CACHE_TTL_SECONDS:
            print(f"[CACHE] Returning cached URL for {video_id}")
            return jsonify({"url": cached["url"]})
        else:
            print(f"[CACHE] Cache expired for {video_id}")
            del stream_cache[video_id]

    # Fetch stream URL with proxy
    try:
        url = get_stream_url_with_proxy_rotation(video_id, proxy_manager)
        if not url:
            return jsonify({"error": "Could not get stream URL"}), 500

        stream_cache[video_id] = {
            "url": url,
            "timestamp": time.time()
        }
        print(f"[CACHE] Cached new stream URL for {video_id}")
        return jsonify({"url": url})
    except Exception as e:
        print(f"[ERROR] Stream error for {video_id}: {str(e)}")
        return jsonify({"error": f"Failed to get stream URL: {str(e)}"}), 500

# Route: /metadata?q=query
@app.route("/metadata", methods=["GET"])
def metadata():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Missing query"}), 400
    try:
        data = get_metadata(query)
        return jsonify(data)
    except Exception as e:
        print(f"[ERROR] Metadata error: {str(e)}")
        return jsonify({"error": f"Failed to fetch metadata: {str(e)}"}), 500

# Route: /trending
@app.route("/trending", methods=["GET"])
def trending():
    global ytmusic
    if not ytmusic:
        try:
            ytmusic = YTMusic()
            print("✅ Re-initialized YTMusic")
        except Exception as e:
            return jsonify({"error": f"YTMusic failed to initialize: {str(e)}"}), 500
    try:
        charts = ytmusic.get_charts()
        return jsonify(charts)
    except Exception as e:
        print(f"[ERROR] Trending error: {str(e)}")
        return jsonify({"error": f"Failed to fetch trending: {str(e)}"}), 500

# Run only for local development
if __name__ == "__main__":
    print("👟 Running local dev server")
    print("✅ Registered routes:", app.url_map)
    app.run(debug=True, port=5000)

# 🔥 In production (like on Render), use:
# gunicorn main:app --bind 0.0.0.0:10000 --workers 1
