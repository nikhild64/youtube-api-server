import json
import os
import subprocess
from urllib.parse import urlparse, parse_qs
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="YouTube Tools API")


class YouTubeTools:
    @staticmethod
    def get_youtube_video_id(url: str) -> Optional[str]:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname

        if hostname == "youtu.be":
            return parsed_url.path[1:]
        if hostname in ("www.youtube.com", "youtube.com"):
            if parsed_url.path == "/watch":
                query_params = parse_qs(parsed_url.query)
                return query_params.get("v", [None])[0]
            if parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2]
            if parsed_url.path.startswith("/v/"):
                return parsed_url.path.split("/")[2]
        return None

    @staticmethod
    def get_video_data(url: str) -> dict:
        try:
            cmd = [
                "yt-dlp",
                "--skip-download",
                "--print-json",
                url,
            ]
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if result.returncode != 0:
                raise HTTPException(
                    status_code=500, detail=f"yt-dlp error: {result.stderr.strip()}"
                )
            metadata = json.loads(result.stdout)
            return {
                "title": metadata.get("title"),
                "uploader": metadata.get("uploader"),
                "duration": metadata.get("duration"),
                "upload_date": metadata.get("upload_date"),
                "description": metadata.get("description"),
                "thumbnail": metadata.get("thumbnail"),
                "view_count": metadata.get("view_count"),
                "like_count": metadata.get("like_count"),
                "channel_url": metadata.get("channel_url"),
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch metadata: {str(e)}"
            )

    @staticmethod
    def get_video_captions(url: str, languages: Optional[List[str]] = None) -> str:
        try:
            lang_opts = []
            if languages:
                lang_opts = ["--sub-lang", ",".join(languages)]
            cmd = [
                "yt-dlp",
                "--skip-download",
                "--write-auto-sub",
                "--sub-format",
                "vtt",
                "--sub-lang",
                ",".join(languages or ["en"]),
                "--output",
                "%(id)s.%(ext)s",
                url,
            ]
            subprocess.run(cmd, check=True)

            video_id = YouTubeTools.get_youtube_video_id(url)
            caption_file = f"{video_id}.en.vtt"
            if not os.path.exists(caption_file):
                raise HTTPException(status_code=404, detail="Captions not found")

            with open(caption_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Clean up file
            os.remove(caption_file)

            caption_lines = [
                line.strip()
                for line in lines
                if line.strip() and not line.strip().isdigit() and "-->" not in line
            ]
            return " ".join(caption_lines)
        except subprocess.CalledProcessError as e:
            raise HTTPException(status_code=500, detail=f"yt-dlp error: {e.stderr}")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error getting captions: {str(e)}"
            )


class YouTubeRequest(BaseModel):
    url: str
    languages: Optional[List[str]] = None


@app.get("/")
async def root():
    return {"message": "YouTube Tools API is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/video-data")
async def video_data(request: YouTubeRequest):
    return YouTubeTools.get_video_data(request.url)


@app.post("/video-captions")
async def video_captions(request: YouTubeRequest):
    return YouTubeTools.get_video_captions(request.url, request.languages)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
