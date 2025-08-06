import os

from vod_context.apply_asr_to_context import apply_asr_to_context
from vod_context.collect_vod_data import crawl_chat_data_for_video
from vod_context.extract_vad import extract_and_save_vad
from vod_context.process_full_context import process_jsonl


def run(video_id: int):
    """before running this function, you need to download the video and extract the audio. reference to collect_vod_data.py

    Args:
        video_id (int): video id
    """
    crawl_chat_data_for_video(video_id)
    extract_and_save_vad(video_id)
    apply_asr_to_context(video_id, model_size="large-v3")
    process_jsonl(video_id)


def init():
    os.makedirs("./data", exist_ok=True)
    os.makedirs("./data/videos", exist_ok=True)
    os.makedirs("./data/audios", exist_ok=True)
    os.makedirs("./data/vads", exist_ok=True)
    os.makedirs("./data/chats", exist_ok=True)
    os.makedirs("./data/full_contexts", exist_ok=True)
