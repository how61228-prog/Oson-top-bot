import asyncio
import uuid
import os
import re
import shutil
import socket
import ssl
import json
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiohttp
import yt_dlp
from config import DOWNLOAD_DIR, BASE_DIR

# ==================== 1. SMART DNS-OVER-HTTPS & IPv4 RESOLVER ====================
_ORIG_GETADDRINFO = socket.getaddrinfo
_DNS_CACHE: Dict[str, str] = {}

DOH_DOMAINS = (
    "instagram.com",
    "cdninstagram.com",
    "fbcdn.net",
    "tiktok.com",
    "tiktokcdn.com",
    "musical.ly",
    "byteoversea.com",
    "ibytedtos.com",
    "youtube.com",
    "youtu.be",
    "googlevideo.com",
    "ytimg.com",
    "soundcloud.com",
    "sndcdn.com",
    "pinterest.com",
    "pinimg.com",
)


def _resolve_via_doh(host: str) -> Optional[str]:
    if not isinstance(host, str):
        return None
    if host in _DNS_CACHE:
        return _DNS_CACHE[host]

    ctx = ssl._create_unverified_context()
    # Try Google DoH via IP 8.8.8.8 first, then Cloudflare 1.1.1.1
    doh_endpoints = [
        (f"https://8.8.8.8/resolve?name={host}&type=A", "dns.google"),
        (f"https://1.1.1.1/dns-query?name={host}&type=A", "cloudflare-dns.com"),
    ]
    for url, host_header in doh_endpoints:
        try:
            req = urllib.request.Request(
                url,
                headers={"Host": host_header, "Accept": "application/dns-json"},
            )
            with urllib.request.urlopen(req, timeout=3, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                for ans in data.get("Answer", []):
                    if ans.get("type") == 1 and ans.get("data"):
                        ip = ans["data"]
                        _DNS_CACHE[host] = ip
                        return ip
        except Exception:
            continue
    return None


def _smart_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    # Force IPv4 (AF_INET) to prevent 40-second IPv6 timeouts on Windows
    target_family = socket.AF_INET if family in (0, socket.AF_UNSPEC, socket.AF_INET) else family

    if isinstance(host, str) and any(d in host.lower() for d in DOH_DOMAINS):
        ip = _resolve_via_doh(host)
        if ip:
            return _ORIG_GETADDRINFO(ip, port, socket.AF_INET, type, proto, flags)

    try:
        res = _ORIG_GETADDRINFO(host, port, target_family, type, proto, flags)
        if res:
            return res
    except Exception:
        ip = _resolve_via_doh(host)
        if ip:
            return _ORIG_GETADDRINFO(ip, port, socket.AF_INET, type, proto, flags)
        raise

    return _ORIG_GETADDRINFO(host, port, family, type, proto, flags)


# Apply global socket patch
socket.getaddrinfo = _smart_getaddrinfo


# ==================== 2. FFMPEG BINARY SETUP ====================
FFMPEG_DIR = BASE_DIR / "bin"
FFMPEG_DIR.mkdir(exist_ok=True)
FFMPEG_EXE = FFMPEG_DIR / "ffmpeg.exe"

try:
    import imageio_ffmpeg
    _src_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    if _src_ffmpeg and os.path.exists(_src_ffmpeg) and not FFMPEG_EXE.exists():
        shutil.copyfile(_src_ffmpeg, FFMPEG_EXE)
    # Linux serverda nusxa bajariladigan bo'lishi kerak
    if FFMPEG_EXE.exists():
        os.chmod(FFMPEG_EXE, 0o755)
except Exception:
    pass


# ==================== 3. URL REGEX & CONSTANTS ====================
URL_REGEX = re.compile(
    r"(https?://[^\s]+)",
    re.IGNORECASE
)

POPULAR_RANDOM_QUERIES = [
    "Konsta Sengacha",
    "Shohruhxon xit qo'shiqlar",
    "Jaloliddin Ahmadaliyev",
    "Hamdam Sobirov",
    "Ozoda Nursaidova",
    "Munisa Rizayeva",
    "Sevara Nazarxon",
    "Miyagi Andy Panda",
    "The Weeknd Blinding Lights",
    "Eminem Mockingbird",
    "Billie Eilish",
    "Imagine Dragons Believer",
    "Coldplay Viva La Vida",
    "Doston Ergashev",
]


def extract_url(text: str) -> Optional[str]:
    match = URL_REGEX.search(text or "")
    if not match:
        return None
    url = match.group(1).rstrip(".,!?)>\"'")
    return url


def is_youtube_watch_url(url: str) -> bool:
    u = url.lower()
    return ("youtube.com/watch" in u or "youtu.be/" in u) and "/shorts/" not in u


def format_duration(seconds: Optional[float]) -> str:
    if not seconds:
        return "00:00"
    sec = int(seconds)
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _base_ydl_opts() -> Dict[str, Any]:
    opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "geo_bypass": True,
        "force_ipv4": True,
        "socket_timeout": 12,
        "retries": 2,
        "concurrent_fragment_downloads": 8,
        "buffersize": 1024 * 64,
        "http_chunk_size": 10485760,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "web"],
                "skip": ["dash", "hls"],
            }
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    if FFMPEG_EXE.exists():
        opts["ffmpeg_location"] = str(FFMPEG_EXE)
    return opts


# ==================== 4. FAST MUSIC SEARCH ====================
async def search_music_yt(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fast flat search on YouTube (takes ~2 seconds) with SoundCloud fallback."""
    def _search():
        opts = _base_ydl_opts()
        opts["extract_flat"] = "in_playlist"

        results = []
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                entries = info.get("entries", []) if info else []
            except Exception:
                entries = []

            if not entries:
                try:
                    info = ydl.extract_info(f"scsearch{limit}:{query}", download=False)
                    entries = info.get("entries", []) if info else []
                except Exception:
                    entries = []

            for e in entries:
                if not e:
                    continue
                vid_id = e.get("id")
                url = e.get("url") or e.get("webpage_url") or (
                    f"https://www.youtube.com/watch?v={vid_id}" if vid_id else ""
                )
                if not url:
                    continue
                title = e.get("title") or "Musiqa"
                duration = e.get("duration")
                uploader = e.get("uploader") or e.get("channel") or "Audio"
                results.append({
                    "id": vid_id or uuid.uuid4().hex[:8],
                    "title": title,
                    "url": url,
                    "duration": format_duration(duration),
                    "uploader": uploader,
                })
            return results

    return await asyncio.to_thread(_search)


# ==================== 5. AUDIO & VIDEO DOWNLOADERS (TURBO SPEED) ====================
def convert_video_to_round(video_path: str) -> Optional[str]:
    """Converts any video file into a 1:1 square, <=59s, 360x360 MP4 suitable for Telegram VideoNote (Dumaloqcha)."""
    if not FFMPEG_EXE.exists() or not os.path.exists(video_path):
        return None
    import subprocess
    out_round = os.path.splitext(video_path)[0] + "_round.mp4"
    try:
        proc = subprocess.run(
            [
                str(FFMPEG_EXE),
                "-y",
                "-t", "59",
                "-i", video_path,
                "-t", "59",
                "-vf", "crop=min(iw\\,ih):min(iw\\,ih),scale=360:360,setsar=1,fps=24",
                "-c:v", "libx264",
                "-profile:v", "baseline",
                "-level", "3.0",
                "-preset", "ultrafast",
                "-crf", "28",
                "-maxrate", "800k",
                "-bufsize", "1600k",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "64k",
                "-ac", "1",
                "-ar", "44100",
                "-movflags", "+faststart",
                out_round,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            import logging
            logging.error(f"FFmpeg round error: {proc.stderr[-400:]}")
        if os.path.exists(out_round) and os.path.getsize(out_round) > 1000:
            return out_round
    except Exception as e:
        import logging
        logging.error(f"convert_video_to_round exception: {e}")
    return None


def extract_audio_from_local_video(video_path: str) -> Optional[str]:
    """Extracts audio from an already-downloaded video file in ~0.4s using local FFmpeg without re-downloading!"""
    if not FFMPEG_EXE.exists() or not os.path.exists(video_path):
        return None
    import subprocess
    out_audio = os.path.splitext(video_path)[0] + "_fast.mp3"
    try:
        subprocess.run(
            [
                str(FFMPEG_EXE),
                "-y",
                "-i", video_path,
                "-vn",
                "-acodec", "libmp3lame",
                "-ab", "128k",
                "-ar", "44100",
                "-threads", "0",
                out_audio,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
            check=True,
        )
        if os.path.exists(out_audio) and os.path.getsize(out_audio) > 1000:
            return out_audio
    except Exception:
        pass
    return None


async def download_audio(url: str) -> Dict[str, Any]:
    """Downloads M4A/MP3 audio at maximum speed (prefers native M4A/MP3 to skip slow re-encoding)."""
    unique_id = uuid.uuid4().hex[:10]
    out_tmpl = str(DOWNLOAD_DIR / f"audio_{unique_id}.%(ext)s")

    def _dl():
        opts = _base_ydl_opts()
        # Prefer native m4a/mp3 around 128kbps (2.5MB instead of 8MB) -> 3x faster download & zero re-encode time!
        opts.update({
            "format": (
                "bestaudio[ext=m4a][abr<=160][filesize<45M]/"
                "bestaudio[ext=mp3][filesize<45M]/"
                "bestaudio[ext=m4a][filesize<45M]/"
                "bestaudio[filesize<45M]/best[filesize<45M]/bestaudio/best"
            ),
            "outtmpl": out_tmpl,
        })

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if "entries" in info and info["entries"]:
                info = info["entries"][0]
            filename = ydl.prepare_filename(info)
            ext = os.path.splitext(filename)[1].lower()

            # Only run FFmpeg if format is webm/opus/mp4 (m4a and mp3 play natively in Telegram Audio Player!)
            if ext not in (".m4a", ".mp3") and FFMPEG_EXE.exists():
                converted = extract_audio_from_local_video(filename)
                if converted:
                    safe_remove(filename)
                    filename = converted

            return {
                "file_path": filename,
                "title": info.get("title") or info.get("track") or "Musiqa",
                "performer": info.get("uploader") or info.get("artist") or info.get("channel") or "Music Bot",
                "duration": int(info.get("duration") or 0),
                "webpage_url": info.get("webpage_url") or url,
            }

    return await asyncio.to_thread(_dl)


async def download_video(url: str, max_seconds: int = 0) -> Dict[str, Any]:
    """Downloads MP4 video optimized for fast Telegram upload (prefers <=720p progressive MP4)."""
    unique_id = uuid.uuid4().hex[:10]
    out_tmpl = str(DOWNLOAD_DIR / f"video_{unique_id}.%(ext)s")

    def _dl():
        opts = _base_ydl_opts()
        opts.update({
            "format": (
                "best[ext=mp4][height<=720][filesize<40M]/"
                "best[ext=mp4][filesize<40M]/"
                "best[filesize<40M]/best"
            ),
            "merge_output_format": "mp4",
            "outtmpl": out_tmpl,
        })
        if max_seconds > 0 and FFMPEG_EXE.exists():
            opts["external_downloader"] = "ffmpeg"
            opts["external_downloader_args"] = {"ffmpeg_i": ["-t", str(max_seconds)]}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if "entries" in info and info["entries"]:
                info = info["entries"][0]
            filename = ydl.prepare_filename(info)
            mp4_candidate = os.path.splitext(filename)[0] + ".mp4"
            final_path = mp4_candidate if os.path.exists(mp4_candidate) else filename

            return {
                "file_path": final_path,
                "title": info.get("title") or info.get("description") or "Video",
                "uploader": info.get("uploader") or info.get("channel") or "Media Bot",
                "duration": int(info.get("duration") or 0),
                "webpage_url": info.get("webpage_url") or url,
            }

    return await asyncio.to_thread(_dl)


# ==================== 6. LYRICS FINDER ====================
async def search_lyrics(query: str) -> Optional[Dict[str, str]]:
    """Fetches song lyrics using LRCLIB public API."""
    api_url = "https://lrclib.net/api/search"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params={"q": query}, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and isinstance(data, list):
                        for item in data:
                            plain = item.get("plainLyrics")
                            if plain:
                                return {
                                    "track": item.get("trackName", query),
                                    "artist": item.get("artistName", ""),
                                    "lyrics": plain[:3800]
                                }
    except Exception:
        pass
    return None


def safe_remove(file_path: Optional[str]):
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
