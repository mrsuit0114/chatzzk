import os
import subprocess
import xml.etree.ElementTree as ET
from typing import Optional

import orjson
import requests
from loguru import logger
from tqdm import tqdm

from config import Config


def load_cookies_from_file(file_path: str) -> Optional[dict]:
    """Load cookies from JSON file with proper error handling."""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Cookie file not found: {file_path}")
            return None

        with open(file_path, "rb") as file:
            cookies = orjson.loads(file.read())
        logger.info(f"✅ Cookies loaded from {file_path}")
        return cookies

    except orjson.JSONDecodeError as e:
        logger.error(f"❌ Error decoding JSON from file {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error loading cookies from {file_path}: {e}")
        return None


class ChzzkStreamExtractor:
    def __init__(self, config: Config):
        self.vod_url = config.ChzzkStream.VOD_URL
        self.vod_info = config.ChzzkStream.VOD_INFO
        self.cookies_file = config.ChzzkStream.COOKIES_FILE
        self.video_dir = config.DataDir.VIDEO_DIR
        self.user_agent = config.Network.USER_AGENT
        self.max_retries = config.Network.HTTP_MAX_RETRIES
        self.timeout = config.Network.HTTP_TIMEOUT

    def extract_streams(self, video_no: int) -> bool:
        """Extract and download VOD streams with proper error handling."""
        try:
            logger.info(f"🎬 Starting VOD extraction for video {video_no}")

            # Get video information
            video_info = self._get_video_info(video_no)
            if not video_info:
                logger.error(f"❌ Failed to get video info for {video_no}")
                return False

            video_id, in_key, metadata = video_info

            # Get stream URL
            stream_url = self._get_stream_url(video_id, in_key)
            if not stream_url:
                logger.error(f"❌ Failed to get stream URL for {video_no}")
                return False

            # Download video
            output_path = os.path.join(self.video_dir, f"{video_no}.mp4")
            success = self._download_video(stream_url, output_path, metadata)

            if success:
                logger.info(f"✅ VOD extraction completed for video {video_no}")
                return True
            else:
                logger.error(f"❌ VOD extraction failed for video {video_no}")
                return False

        except Exception as e:
            logger.error(f"❌ Unexpected error during VOD extraction for {video_no}: {e}")
            return False

    def _get_video_info(self, video_no: int) -> Optional[tuple[str, str, dict]]:
        """Get video information from API with retry logic."""
        api_url = self.vod_info.format(video_no=video_no)
        headers = {"User-Agent": self.user_agent}

        for attempt in range(self.max_retries):
            try:
                response = requests.get(api_url, headers=headers, timeout=self.timeout)
                response.raise_for_status()

                if response.status_code == 404:
                    logger.error(f"❌ Video {video_no} not found")
                    return None

                content = response.json().get("content", {})
                video_id = content.get("videoId")
                in_key = content.get("inKey")

                if video_id and in_key:
                    metadata = {
                        "author": content.get("channel", {}).get("channelName", "Unknown"),
                        "title": content.get("videoTitle", "Unknown"),
                        "category": content.get("videoCategory", "Unknown"),
                    }
                    logger.info(f"📹 Video info: {metadata['author']} - {metadata['title']}")
                    return video_id, in_key, metadata

                # Try with cookies if login required
                logger.info("🔐 Login required, attempting with cookies...")
                cookies = load_cookies_from_file(self.cookies_file)
                if cookies:
                    response = requests.get(api_url, cookies=cookies, headers=headers, timeout=self.timeout)
                    response.raise_for_status()
                    content = response.json().get("content", {})
                    video_id = content.get("videoId")
                    in_key = content.get("inKey")

                    if video_id and in_key:
                        metadata = {
                            "author": content.get("channel", {}).get("channelName", "Unknown"),
                            "title": content.get("videoTitle", "Unknown"),
                            "category": content.get("videoCategory", "Unknown"),
                        }
                        logger.info(f"📹 Video info (with cookies): {metadata['author']} - {metadata['title']}")
                        return video_id, in_key, metadata

                logger.error(f"❌ Failed to get video ID and in_key for {video_no}")
                return None

            except requests.RequestException as e:
                logger.warning(f"⚠️ API request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"❌ Failed to fetch video information after {self.max_retries} attempts")
                    return None
                continue
            except orjson.JSONDecodeError as e:
                logger.error(f"❌ Failed to decode JSON response: {e}")
                return None
            except Exception as e:
                logger.error(f"❌ Unexpected error getting video info: {e}")
                return None

        return None

    def _get_stream_url(self, video_id: str, in_key: str) -> Optional[str]:
        """Get stream URL from DASH manifest."""
        try:
            video_url = self.vod_url.format(video_id=video_id, in_key=in_key)
            response = requests.get(video_url, headers={"Accept": "application/dash+xml"}, timeout=self.timeout)
            response.raise_for_status()

            root = ET.fromstring(response.text)
            ns = {"mpd": "urn:mpeg:dash:schema:mpd:2011", "nvod": "urn:naver:vod:2020"}

            representations = []
            for rep in root.findall(".//mpd:Representation", namespaces=ns):
                width = rep.get("width")
                height = rep.get("height")
                if width and height:
                    resolution = min(int(width), int(height))
                    base_url_elem = rep.find(".//mpd:BaseURL", namespaces=ns)
                    if base_url_elem is not None and base_url_elem.text:
                        base_url = base_url_elem.text
                        if not base_url.endswith("/hls/"):
                            representations.append([resolution, base_url])

            if not representations:
                logger.error("❌ No valid stream representations found")
                return None

            # Sort by resolution and get lowest (for audio extraction)
            representations.sort(key=lambda x: x[0])
            stream_url = representations[0][1]
            logger.info(f"🔗 Stream URL obtained: {stream_url}")
            return stream_url

        except Exception as e:
            logger.error(f"❌ Failed to get stream URL: {e}")
            return None

    def _download_video(self, video_url: str, output_path: str, metadata: dict) -> bool:
        """Download video with memory-efficient streaming."""
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Get file size
            with requests.Session() as session:
                response = session.head(video_url, timeout=self.timeout)
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))

                if total_size == 0:
                    logger.error("❌ Failed to get file size")
                    return False

                logger.info(f"📥 Starting download: {total_size / (1024 * 1024):.1f} MB")

                # Download with progress bar
                with session.get(video_url, stream=True, timeout=self.timeout) as r:
                    r.raise_for_status()

                    with open(output_path, "wb") as f:
                        with tqdm(total=total_size, unit="B", unit_scale=True, desc="Downloading") as pbar:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    pbar.update(len(chunk))

                logger.info(f"✅ Download completed: {output_path}")
                return True

        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            # Clean up partial file
            if os.path.exists(output_path):
                os.remove(output_path)
            return False

    def download_from_direct_url(self, mp4_url: str, video_no: int) -> bool:
        """Download MP4 directly using curl -L when a full URL is provided."""
        output_path = os.path.join(self.video_dir, f"{video_no}.mp4")
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            logger.info(f"📥 Downloading direct VOD URL for video {video_no}")
            result = subprocess.run(
                ["curl", "-L", mp4_url, "-o", output_path],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.error(f"❌ curl download failed (code {result.returncode}): {result.stderr.strip()}")
                if os.path.exists(output_path):
                    os.remove(output_path)
                return False

            logger.info(f"✅ Download completed: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Direct download failed: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
