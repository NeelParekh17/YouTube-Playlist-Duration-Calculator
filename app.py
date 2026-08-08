import os
import re
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, jsonify, send_from_directory
import yt_dlp


app = Flask(__name__, static_folder="static")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def extract_video_id(text: str) -> str | None:
    """
    If 'text' looks like a YouTube URL, return its video ID.
    Handles youtu.be/ID, watch?v=ID, /shorts/ID, /embed/ID, /live/ID.
    Returns None if it's not a URL.
    """
    text = text.strip()
    patterns = [
        r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([A-Za-z0-9_-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    return None


def resolve_input(raw: str) -> dict:
    """
    Given a raw string (title or URL), return:
      { "type": "url"|"title", "video_id": str|None, "raw": str }
    """
    vid_id = extract_video_id(raw)
    if vid_id:
        return {"type": "url", "video_id": vid_id, "raw": raw}
    return {"type": "title", "video_id": None, "raw": raw}


def fetch_playlist_info(playlist_url: str) -> list[dict]:
    """Fetch all videos (title, duration, id) from a YouTube playlist."""
    flat_opts = {
        "quiet": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(flat_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)

    if not info or "entries" not in info:
        return []

    videos = []
    missing = []

    for entry in info["entries"]:
        if entry is None:
            continue
        vid_id = entry.get("id", "")
        title = entry.get("title") or "Unknown"
        duration = entry.get("duration")
        videos.append({
            "title": title,
            "duration": int(duration) if duration is not None else None,
            "id": vid_id,
            "url": f"https://www.youtube.com/watch?v={vid_id}",
        })
        if duration is None:
            missing.append(vid_id)

    # Fallback: fetch individually for any missing durations
    if missing:
        single_opts = {"quiet": True, "skip_download": True, "ignoreerrors": True}
        with yt_dlp.YoutubeDL(single_opts) as ydl:
            for video in videos:
                if video["duration"] is None:
                    try:
                        vinfo = ydl.extract_info(video["url"], download=False)
                        if vinfo:
                            video["duration"] = int(vinfo.get("duration") or 0)
                            video["title"] = vinfo.get("title") or video["title"]
                    except Exception:
                        video["duration"] = 0

    return [v for v in videos if v.get("duration")]


def fuzzy_match(query: str, title: str) -> bool:
    return query.strip().lower() in title.strip().lower()


def find_video_index(all_videos: list[dict], resolved: dict) -> int | None:
    """Find the index of a video in the playlist, by URL id or fuzzy title."""
    if resolved["type"] == "url":
        vid_id = resolved["video_id"]
        for i, v in enumerate(all_videos):
            if v["id"] == vid_id:
                return i
        return None
    else:
        query = resolved["raw"]
        for i, v in enumerate(all_videos):
            if fuzzy_match(query, v["title"]):
                return i
        return None


def format_duration(total_seconds: int) -> dict:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return {
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "formatted": " ".join(parts),
        "total_seconds": total_seconds,
    }


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/calculate", methods=["POST"])
def calculate():
    data = request.get_json()
    playlist_url = (data.get("playlist_url") or "").strip()
    inputs_raw = data.get("inputs", [])   # list of strings (titles or URLs)
    mode_hint = (data.get("mode") or "auto").strip()
    # mode_hint: "auto" | "range" | "individual"

    if not playlist_url:
        return jsonify({"error": "Playlist URL is required"}), 400

    try:
        all_videos = fetch_playlist_info(playlist_url)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch playlist: {str(e)}"}), 500

    if not all_videos:
        return jsonify({
            "error": "No videos found (playlist may be private, empty, or unavailable)"
        }), 404

    inputs = [i.strip() for i in inputs_raw if i.strip()]

    # ── No inputs → full playlist ──────────────────────────────────────────
    if not inputs:
        total_seconds = sum(v["duration"] for v in all_videos)
        return jsonify({
            "playlist_total_videos": len(all_videos),
            "selected_videos": all_videos,
            "selected_count": len(all_videos),
            "duration": format_duration(total_seconds),
            "not_found": [],
            "mode": "full_playlist",
            "range_start": None,
            "range_end": None,
        })

    resolved = [resolve_input(i) for i in inputs]

    # ── Exactly 2 inputs → range mode ─────────────────────────────────────
    if len(resolved) == 2 and mode_hint != "individual":
        idx_a = find_video_index(all_videos, resolved[0])
        idx_b = find_video_index(all_videos, resolved[1])

        not_found = []
        if idx_a is None:
            not_found.append(inputs[0])
        if idx_b is None:
            not_found.append(inputs[1])

        if idx_a is None or idx_b is None:
            # Fall back: return only what was found
            found_videos = []
            if idx_a is not None:
                found_videos.append(all_videos[idx_a])
            if idx_b is not None:
                found_videos.append(all_videos[idx_b])
            total_seconds = sum(v["duration"] for v in found_videos)
            return jsonify({
                "playlist_total_videos": len(all_videos),
                "selected_videos": found_videos,
                "selected_count": len(found_videos),
                "duration": format_duration(total_seconds),
                "not_found": not_found,
                "mode": "range",
                "range_start": all_videos[idx_a]["title"] if idx_a is not None else inputs[0],
                "range_end": all_videos[idx_b]["title"] if idx_b is not None else inputs[1],
            })

        start = min(idx_a, idx_b)
        end = max(idx_a, idx_b)
        selected_videos = all_videos[start: end + 1]
        total_seconds = sum(v["duration"] for v in selected_videos)

        return jsonify({
            "playlist_total_videos": len(all_videos),
            "selected_videos": selected_videos,
            "selected_count": len(selected_videos),
            "duration": format_duration(total_seconds),
            "not_found": [],
            "mode": "range",
            "range_start": all_videos[start]["title"],
            "range_end": all_videos[end]["title"],
        })

    # ── 1 or 3+ inputs → individual matches ───────────────────────────────
    matched_videos = []
    not_found = []

    for res in resolved:
        if res["type"] == "url":
            vid_id = res["video_id"]
            match = next((v for v in all_videos if v["id"] == vid_id), None)
            if match:
                matched_videos.append(match)
            else:
                not_found.append(res["raw"])
        else:
            matches = [v for v in all_videos if fuzzy_match(res["raw"], v["title"])]
            if matches:
                matched_videos.extend(matches)
            else:
                not_found.append(res["raw"])

    # Deduplicate preserving order
    seen = set()
    deduped = []
    for v in matched_videos:
        if v["id"] not in seen:
            seen.add(v["id"])
            deduped.append(v)

    total_seconds = sum(v["duration"] for v in deduped)
    return jsonify({
        "playlist_total_videos": len(all_videos),
        "selected_videos": deduped,
        "selected_count": len(deduped),
        "duration": format_duration(total_seconds),
        "not_found": not_found,
        "mode": "individual",
        "range_start": None,
        "range_end": None,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)


