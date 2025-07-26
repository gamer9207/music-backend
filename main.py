import time
from flask import Flask, jsonify, request, redirect, Response
from flask_cors import CORS
from yt.stream import get_stream_url_with_proxy_rotation
from yt.metadata import get_metadata
from proxies.proxy_manager import ProxyManager
from ytmusicapi import YTMusic
import requests

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Globals
proxy_manager = ProxyManager()
stream_cache = {}  # { video_id: { "url": ..., "timestamp": ... } }
CACHE_TTL_SECONDS = 3600  # 1 hour

# YTMusic initialization
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

# Favicon route
@app.route("/favicon.ico")
def favicon():
    return '', 204

# 🔍 /metadata?q=search+term
@app.route("/metadata", methods=["GET"])
def metadata():
    query = request.args.get("q")
    print(f"[METADATA] Query: {query}")

    if not query:
        return jsonify({"error": "Missing query"}), 400
    try:
        data = get_metadata(query)
        return jsonify(data)
    except Exception as e:
        print(f"[ERROR] Metadata fetch failed: {e}")
        return jsonify({"error": f"Metadata error: {str(e)}"}), 500

# 🔊 /stream?video_id=xyz (returns JSON URL)
@app.route("/stream", methods=["GET"])
def stream_json():
    video_id = request.args.get("video_id")
    print(f"[STREAM:JSON] video_id: {video_id}")

    if not video_id:
        return jsonify({"error": "Missing video ID"}), 400

    # Cache hit
    cached = stream_cache.get(video_id)
    if cached:
        age = time.time() - cached["timestamp"]
        if age < CACHE_TTL_SECONDS:
            print(f"[CACHE] Returning cached stream URL for {video_id}")
            return jsonify({"url": cached["url"]})
        else:
            print(f"[CACHE] Expired for {video_id}")
            del stream_cache[video_id]

    # Fetch new stream URL
    try:
        url = get_stream_url_with_proxy_rotation(video_id, proxy_manager)
        if not url:
            raise ValueError("No URL returned from stream fetch")

        stream_cache[video_id] = {
            "url": url,
            "timestamp": time.time()
        }
        print(f"[CACHE] Stored stream URL for {video_id}")
        return jsonify({"url": url})
    except Exception as e:
        print(f"[ERROR] Failed to fetch stream for {video_id}: {e}")
        return jsonify({"error": f"Stream fetch failed: {str(e)}"}), 500

# 🔁 /stream/<video_id> (redirects directly to audio)
@app.route("/stream/<video_id>", methods=["GET"])
def stream_redirect(video_id):
    print(f"[STREAM:REDIRECT] video_id: {video_id}")

    # Cache hit
    cached = stream_cache.get(video_id)
    if cached:
        age = time.time() - cached["timestamp"]
        if age < CACHE_TTL_SECONDS:
            print(f"[CACHE] Redirecting to cached URL for {video_id}")
            return redirect(cached["url"])
        else:
            print(f"[CACHE] Expired for {video_id}")
            del stream_cache[video_id]

    # Fetch and redirect
    try:
        url = get_stream_url_with_proxy_rotation(video_id, proxy_manager)
        if not url:
            raise ValueError("No stream URL returned")
        stream_cache[video_id] = {
            "url": url,
            "timestamp": time.time()
        }
        print(f"[REDIRECT] Redirecting to stream URL for {video_id}")
        return redirect(url)
    except Exception as e:
        print(f"[ERROR] Redirect stream failed for {video_id}: {e}")
        return jsonify({"error": f"Stream redirect failed: {str(e)}"}), 500

# 🔁 /proxy-stream?url=encoded_audio_url (stream audio through server)
@app.route("/proxy-stream", methods=["GET"])
def proxy_stream():
    stream_url = request.args.get("url")
    if not stream_url:
        return jsonify({"error": "Missing stream URL"}), 400

    print(f"[PROXY-STREAM] Proxying stream from: {stream_url}")

    def generate():
        with requests.get(stream_url, stream=True) as r:
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk

    return Response(generate(), content_type="audio/webm")

# 🔥 /trending
@app.route("/trending", methods=["GET"])
def trending():
    global ytmusic
    print("[TRENDING] Fetching trending charts")

    if not ytmusic:
        try:
            ytmusic = YTMusic()
            print("✅ YTMusic reinitialized")
        except Exception as e:
            print(f"[ERROR] Failed to reinitialize YTMusic: {e}")
            return jsonify({"error": f"YTMusic init failed: {str(e)}"}), 500
    try:
        charts = ytmusic.get_charts()
        return jsonify(charts)
    except Exception as e:
        print(f"[ERROR] Trending fetch failed: {e}")
        return jsonify({"error": f"Trending error: {str(e)}"}), 500

# Catch-all route
@app.route("/<path:path>")
def catch_all(path):
    return jsonify({"catch": path}), 200

# 🧪 Local dev only
if __name__ == "__main__":
    print("👟 Starting development server")
    print("✅ Registered routes:", app.url_map)
    app.run(debug=True, port=5000)

# 🛠️ Production example:
# gunicorn main:app --bind 0.0.0.0:10000 --workers 1
