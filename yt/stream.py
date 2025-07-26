import yt_dlp
from cachetools import TTLCache
from proxies.proxy_manager import ProxyManager

# ✅ Initialize proxy manager
proxy_manager = ProxyManager()

# ✅ Cache: max 1000 items, TTL 30 minutes
stream_cache = TTLCache(maxsize=1000, ttl=1800)

def get_stream_url_with_proxy_rotation(video_id: str, proxy_manager: ProxyManager):
    if not video_id:
        print("[❌ ERROR] video_id is missing or empty.")
        return None

    # ✅ Check cache
    if video_id in stream_cache:
        print(f"[CACHE ✅] Returning cached stream URL for: {video_id}")
        return stream_cache[video_id]

    proxies_tried = set()
    max_attempts = 10

    # 🔁 Try proxy-based requests
    for attempt in range(max_attempts):
        proxy = proxy_manager.get_proxy()

        if not proxy or proxy in proxies_tried:
            print(f"[PROXY ❌] No usable proxy or already tried: {proxy}")
            break

        proxies_tried.add(proxy)
        print(f"[yt_dlp 🔁] Attempt {attempt + 1}: Using proxy {proxy}")

        ydl_opts = {
            'quiet': True,
            'format': 'bestaudio/best',
            'skip_download': True,
            'noplaylist': True,
            'proxy': proxy,
            'retries': 0,  
            'socket_timeout': 5,
            'nocheckcertificate': True,
            'cookiefile': 'cookies.txt'
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                stream_url = info.get("url")

                if stream_url:
                    print(f"[✅ SUCCESS] Fetched stream URL via proxy: {proxy}")
                    stream_cache[video_id] = stream_url
                    return stream_url
                else:
                    print(f"[❌ FAIL] No stream URL returned (proxy: {proxy})")

        except yt_dlp.utils.DownloadError as e:
            print(f"[yt_dlp ❌] DownloadError using proxy {proxy}: {e}")
            proxy_manager.remove_proxy(proxy)
        except Exception as e:
            print(f"[yt_dlp ❌] Unknown error using proxy {proxy}: {e}")
            proxy_manager.remove_proxy(proxy)

    # 🔄 Fallback: try direct connection
    print("[FALLBACK ⚠️] All proxies failed. Trying direct connection...")

    try:
        ydl_opts = {
           'quiet': True,
            'format': 'bestaudio/best',
            'noplaylist': True,
            'skip_download': True,
            'retries': 0,  # ⛔ Disable retry on fallback too
            'socket_timeout': 5,
            'nocheckcertificate': True,
            'cookiefile': 'cookies.txt'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            stream_url = info.get("url")

            if stream_url:
                print(f"[✅ SUCCESS] Fetched stream URL without proxy.")
                stream_cache[video_id] = stream_url
                return stream_url
            else:
                print("[❌ FAIL] No stream URL returned (no proxy).")

    except yt_dlp.utils.DownloadError as e:
        print(f"[yt_dlp ❌] Direct DownloadError: {e}")
    except Exception as e:
        print(f"[yt_dlp ❌] Direct unknown error: {e}")

    return None
