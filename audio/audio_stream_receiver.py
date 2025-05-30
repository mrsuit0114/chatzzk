import threading

import ffmpeg
from loguru import logger

from audio.circular_audio_buffer import CircularAudioBuffer


class AudioStreamReceiver:
    """Fetch m3u8 stream, decode audio with ffmpeg, and write raw audio bytes into a circular buffer."""

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
        while self.is_running and not self.stop_event.is_set():
            try:
                if not self.process or not self.process.stdout:
                    logger.error("[Receiver] Process or stdout not available.")
                    break
                raw_audio = self.process.stdout.read(self.ffmpeg_read_chunk_size)
                if not raw_audio:
                    logger.error("[Receiver] FFMPEG stream ended or no more data")
                    break
                self.buffer.write(raw_audio)
            except Exception as e:
                logger.error(f"[Receiver] Error reading audio stream: {e}")
                break
        logger.info("[Receiver] Audio stream reader stopped")
        self.stop_event.set()

    def start(self) -> None:
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
