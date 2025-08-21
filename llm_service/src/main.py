from common.clients.storage import MinioStorageClient
from common.utils.data_loader import DataLoader

from config import Config
from llm_tasks import LLMTask
from services import LLMService
from utils.data_processor import DataProcessor

PROMPT_BUILDER_TYPE = "langfuse"
LLM_CLIENT_TYPE = "litellm"
TASK_DATA = {
    "broadcast_metadata": {
        "category": "Just Chatting",
        "streamer_name": "김동현",
        "streamer_nicknames": ["동현이햄", "동현"],
        "fan_nicknames": ["멍청자", "김청자"],
        "streamer_infos": [
            "피부에 트러블이 많아 곰보로 놀림받음",
            "뽐낼 때 '오티형이야'라는 말이 사용됨",
        ],
    },
    "platform_metadata": {"platform_name": "치지직", "donation_currency": "치즈"},
}

VIDEO_NO = 12341234

config = Config()


def main():
    import os

    import orjson

    llm_task = LLMTask(PROMPT_BUILDER_TYPE, LLM_CLIENT_TYPE)
    storage_client = MinioStorageClient(config.storage_config)
    data_loader = DataLoader(storage_client)
    data_processor = DataProcessor(config)

    llm_service = LLMService(llm_task, data_loader, data_processor)
    short_term_summarise = llm_service.generate_full_summary(VIDEO_NO, TASK_DATA)

    # Convert list of SummarySegment (Pydantic models) to list of dicts
    summary_dicts = [segment.model_dump() for segment in short_term_summarise]

    # Prepare output directory and file path
    output_dir = "./data/summaries"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{VIDEO_NO}.json")

    data_to_save = {"short_term_summary": summary_dicts}

    # orjson.dumps()는 바이트를 반환하므로, 이를 파일에 직접 씁니다.
    json_bytes = orjson.dumps(data_to_save, option=orjson.OPT_INDENT_2)

    with open(output_path, "wb") as f:  # 파일 모드를 'w' 대신 'wb'로 변경
        f.write(json_bytes)


main()
