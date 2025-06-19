import fcntl
import os
import select
import threading
import time

import ffmpeg
from loguru import logger

from context.audio.circular_audio_buffer import CircularAudioBuffer


class AudioStreamReceiver:
    """Fetch m3u8 stream, decode audio with ffmpeg, and write raw audio bytes into a circular buffer."""

    SELECT_TIMEOUT_S = 0.1
    WRITE_INTERVAL_S = 1.0

    def __init__(
        self, m3u8_url: str, buffer: CircularAudioBuffer, target_sampling_rate: int, ffmpeg_read_chunk_size: int
    ):
        self.m3u8_url: str = m3u8_url
        self.buffer = buffer
        self.target_sampling_rate: int = target_sampling_rate
        self.ffmpeg_read_chunk_size: int = ffmpeg_read_chunk_size

        self.process = None
        self.is_running = False
        self.stop_event = threading.Event()
        self.reader_audio_stream_thread = None

    def _reader_audio_stream(self) -> None:
        """
        Reads audio data from ffmpeg's stdout and writes it to the buffer.
        Runs in a background thread until stopped or the stream ends.
        """
        if self.process and self.process.stdout:
            fd = self.process.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        else:
            logger.error("[Receiver] Process or stdout not available.")
            return

        internal_buffer = bytearray()
        last_write_time = time.time()

        while self.is_running and not self.stop_event.is_set():
            readable, _, _ = select.select([self.process.stdout], [], [], self.SELECT_TIMEOUT_S)
            if readable:
                try:
                    chunk = self.process.stdout.read(self.ffmpeg_read_chunk_size)
                    if chunk:
                        internal_buffer.extend(chunk)
                        last_write_time = time.time()
                except Exception as e:
                    logger.error(f"[Receiver] Error reading audio stream: {e}")
                    break

            if time.time() - last_write_time > self.WRITE_INTERVAL_S and internal_buffer:
                self.buffer.write(bytes(internal_buffer))
                internal_buffer.clear()
                last_write_time = time.time()

        if internal_buffer:
            self.buffer.write(bytes(internal_buffer))
            internal_buffer.clear()

        logger.info("[Receiver] Audio stream reader stopped")
        self.stop_event.set()

    def run(self) -> None:
        self.is_running = True
        self.stop_event.clear()

        try:
            self.process = (
                ffmpeg.input(self.m3u8_url, protocol_whitelist="file,http,https,tcp,tls")
                .output("pipe:", format="s16le", acodec="pcm_s16le", ac=1, ar=self.target_sampling_rate)
                .global_args("-fflags", "nobuffer")
                .global_args("-loglevel", "error")
                .run_async(pipe_stdout=True, pipe_stderr=False)
            )
        except Exception as e:
            logger.error(f"[Receiver] Error starting FFMPEG process: {e}")
            self.stop_event.set()
            raise

        self.reader_audio_stream_thread = threading.Thread(target=self._reader_audio_stream)
        self.reader_audio_stream_thread.daemon = True
        self.reader_audio_stream_thread.start()

    def stop(self) -> None:
        if not self.is_running:
            return
        logger.info("[Receiver] Stopping AudioStreamReceiver...")
        self.is_running = False
        self.stop_event.set()

        if self.reader_audio_stream_thread and self.reader_audio_stream_thread.is_alive():
            self.reader_audio_stream_thread.join(timeout=5.0)
            logger.info("[Receiver] Reader thread stopped.")

        if self.process:
            logger.info("[Receiver] Terminating FFMPEG process...")
            try:
                self.process.stdout.close()
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception as e:
                logger.error(f"[Receiver] Error terminating FFMPEG process: {e}")
            logger.info("[Receiver] FFMPEG process terminated.")
