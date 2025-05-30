import requests
from loguru import logger

from audio.audio_processor import AudioProcessor
from audio.audio_stream_receiver import AudioStreamReceiver
from audio.circular_audio_buffer import CircularAudioBuffer
from data_types.context_data import ContextData


def _get_audio_m3u8_url(channel_id: str, m3u8_proxy_url: str) -> str:
    """Get audio m3u8 url from channel_id and m3u8_proxy_url."""
    proxy_url = m3u8_proxy_url.format(channel_id=channel_id)

    response = requests.get(proxy_url, allow_redirects=False)

    if response.status_code == 302:
        m3u8_url = response.headers.get("Location")
        if m3u8_url is None:
            logger.error("Failed to get m3u8 URL")
            raise Exception("Failed to get m3u8 URL")
        logger.info(f"m3u8 URL: {m3u8_url}")
        audio_url = m3u8_url.replace("/1080p/", "/audioOnly/")
        return audio_url
    else:
        logger.error(f"Failed to get m3u8 URL: {response.status_code} {response.text}")
        raise Exception(f"Failed to get m3u8 URL: {response.status_code} {response.text}")


class AudioStreamProcessor:
    """
    AudioStreamProcessor is responsible for receiving audio stream from the channel and processing it.
    It uses AudioStreamReceiver to receive audio stream and AudioProcessor to process it.
    """

    def __init__(self, channel_id: str, audio_config: dict):
        self.m3u8_url: str = _get_audio_m3u8_url(channel_id, audio_config["m3u8_proxy_url"])
        self.buffer = CircularAudioBuffer(
            audio_config["target_sampling_rate"] * audio_config["bytes_per_sample"] * audio_config["buffer_duration_s"]
        )

        self.processor = AudioProcessor(audio_config, self.buffer)
        self.receiver = AudioStreamReceiver(
            self.m3u8_url, self.buffer, audio_config["target_sampling_rate"], audio_config["ffmpeg_read_chunk_size"]
        )

    def run(self) -> None:
        try:
            self.receiver.start()
            self.processor.start()

            while True:
                try:
                    self.receiver.stop_event.wait(timeout=1.0)
                    if self.receiver.stop_event.is_set():
                        break
                except KeyboardInterrupt:
                    logger.info("\nCtrl+C detected. Stopping application...")
                    break
        finally:
            self.stop()

    def stop(self) -> None:
        logger.info("\nStopping AudioStreamProcessor...")
        self.receiver.stop()
        self.processor.stop()
        logger.info("AudioStreamProcessor stopped cleanly.")

    def get_context_audio(self) -> list[ContextData]:
        return self.processor.get_context_audio()
