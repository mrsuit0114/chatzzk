import asyncio
import shutil
from pathlib import Path
from urllib.parse import urljoin

import aiofiles
import ffmpeg
from loguru import logger

from chatzzk_clients._http.aiohttp_client import AioHTTPClient
from chatzzk_core.schemas.config.clients.media_processor import MediaProcessorConfig


class MediaProcessor:
    def __init__(self, config: MediaProcessorConfig, http_client: AioHTTPClient | None = None):
        self._http_client = http_client
        self.target_channels = config.target_channels
        self.target_sample_rate = config.target_sample_rate
        self.acodec = config.acodec
        self.worker_num = config.worker_num
        self.chunk_size = config.chunk_size

    # mp4 url, m3u8 url에 따른 다운로드, load_audio
    async def extract_wav_from_mp4_url(self, mp4_url: str, output_wav_path: str | Path) -> None:
        """
        Downloads an mp4 from the given URL and extracts audio as a WAV file to output_wav_path.
        """
        try:
            stream = (
                ffmpeg.input(mp4_url)
                .output(
                    str(output_wav_path),
                    acodec=self.acodec,
                    ar=self.target_sample_rate,
                    ac=self.target_channels,
                    vn=None,
                    loglevel="error",
                )
                .overwrite_output()
            )
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: ffmpeg.run(stream, capture_stderr=True))

            logger.success(f"✅ WAV audio extracted from '{mp4_url}' to '{output_wav_path}'")
        except ffmpeg.Error as e:
            logger.error(f"❌ ffmpeg error extracting wav from '{mp4_url}': {e.stderr.decode('utf8', errors='ignore')}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to extract wav from '{mp4_url}': {e}")
            raise

    async def download_m3u8_and_extract_wav(
        self, m3u8_url: str, tmp_dir: str, video_path: str, output_wav_path: str, cleanup: bool = True
    ) -> str:
        tmp_dir = Path(tmp_dir)
        video_path = Path(video_path)
        output_wav_path = Path(output_wav_path)

        if self._http_client is None:
            raise RuntimeError("HTTP Client is required for M3U8 download.")

        async with self._http_client.get(m3u8_url) as response:
            content = await response.text()
        lines = content.splitlines()
        segments = [line for line in lines if line and not line.startswith("#")]
        format_num = len(str(len(segments)))

        await self._download_init_segment(lines, tmp_dir, m3u8_url, format_num)
        await self._download_segments(segments, tmp_dir, m3u8_url, format_num)
        await self._merge_segments(tmp_dir, video_path)
        await self.extract_wav_cleanup_video(video_path, output_wav_path, cleanup)

    async def _download_init_segment(self, lines: list[str], tmp_dir: Path, base_m3u8_url: str, format_num: int):
        init_segment = None
        for line in lines:
            if line.startswith("#EXT-X-MAP:"):
                init_segment = line.split("URI=")[1].strip('"')
                break
        if not init_segment:
            logger.error("❌ Init segment not found in m3u8 playlist.")
            raise Exception("No #EXT-X-MAP found")
        init_url = urljoin(base_m3u8_url, init_segment)
        init_segment_path = tmp_dir / f"{0:0{format_num}d}.m4s"

        async with self._http_client.get(init_url) as response:
            content = await response.read()
            async with aiofiles.open(init_segment_path, "wb") as f:
                await f.write(content)

        logger.info(f"✅ Init segment saved: {init_segment_path}")

    async def _download_segments(self, segments: list[str], tmp_dir: Path, base_m3u8_url: str, format_num: int):
        sem = asyncio.Semaphore(self.worker_num)

        async def download_one(index: int, segment_url: str):
            async with sem:
                full_url = urljoin(base_m3u8_url, segment_url)
                segment_path = tmp_dir / f"{index:0{format_num}d}.m4s"

                async with self._http_client.get(full_url) as response:
                    content = await response.read()
                    async with aiofiles.open(segment_path, "wb") as f:
                        await f.write(content)

        tasks = [download_one(idx + 1, segment) for idx, segment in enumerate(segments)]

        try:
            return await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"❌ 일부 세그먼트 다운로드 실패: {e}")
            raise

    async def _merge_segments(self, tmp_dir: Path, video_path: Path):
        """
        tmp_path에 저장된 세그먼트 파일을 순서대로 병합하여 video_path(MP4) 생성
        """
        try:
            segment_files = sorted(tmp_dir.glob("*.m4s"), key=lambda p: int(p.stem))

            if not segment_files:
                logger.error(f"❌ 병합할 세그먼트 파일이 존재하지 않음: {tmp_dir}")
                raise Exception("No segment files found for merging.")

            async with aiofiles.open(video_path, "wb") as final_f:
                for seg_path in segment_files:
                    async with aiofiles.open(seg_path, "rb") as seg_f:
                        while True:
                            chunk = await seg_f.read(self.chunk_size)
                            if not chunk:
                                break
                            await final_f.write(chunk)

            logger.info(f"✅ Segments merged: {video_path}")

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, shutil.rmtree, tmp_dir)
            logger.info(f"✅ tmp_dir cleaned: {tmp_dir}")

        except Exception as e:
            logger.error(f"Error during merge: {e}")
            raise

    async def extract_wav_cleanup_video(self, mp4_path: Path, wav_path: Path, cleanup: bool) -> Path:
        """MP4에서 WAV 추출 및 mp4 삭제"""
        stream = (
            ffmpeg.input(str(mp4_path))
            .output(
                str(wav_path),
                acodec=self.acodec,
                ar=self.target_sample_rate,
                ac=self.target_channels,
                vn=None,
                loglevel="error",
            )
            .overwrite_output()
        )

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: ffmpeg.run(stream, capture_stderr=True))

        try:
            if cleanup:
                mp4_path.unlink(missing_ok=True)
                logger.info(f"✅ mp4 file '{mp4_path}' deleted")
        except Exception as e:
            logger.warning(f"❌ mp4 file deletion failed: {e}")

        return wav_path
