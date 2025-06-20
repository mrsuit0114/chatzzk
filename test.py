import json
import os
import time
from collections import deque
from itertools import groupby
from typing import Generator

from llm.llm_client import LLMClient


def _group_by_time_interval(context_file: str, interval_ms: int = 120000) -> Generator[list[dict], None, None]:
    with open(context_file, encoding="utf-8") as f:
        # 모든 메시지를 읽어서 리스트로 저장
        messages = []
        for line in f:
            if line.strip():
                message = json.loads(line)
                messages.append(message)

        # timestamp를 interval_ms로 나눈 몫을 기준으로 그룹화
        for _, group in groupby(messages, key=lambda x: x["timestamp"] // interval_ms):
            yield list(group)


def _get_context_prompt(context_list: list[dict]) -> str:
    context = ""
    for ele in context_list:
        pay_amount = ele["pay_amount"]
        if pay_amount == -1:
            context += f"[ASR] {ele['text']}\n"
        elif pay_amount == 0:
            context += f"[CHAT] {ele['text']}\n"
        else:
            context += f"[DONATION] {ele['text']}\n"
    return context


if __name__ == "__main__":
    summary_filename_gpt = "./data/summaries/gpt-4o-mini_summary_7438744_{prefix}.json"
    summary_filename_gemini = "./data/summaries/gemini-2.0-flash_summary_7438744_{prefix}.json"

    context_file = "data/full_contexts/whisperx_large-v3_full_context_7438744.jsonl"
    with open("llm/config.json", encoding="utf-8") as f:
        config = json.load(f)
    proxy_url = "http://0.0.0.0:4000"
    llm_client = LLMClient(config, proxy_url)
    metadata = {
        "category": "잡담",
        "streamer_name": "아라하시 타비",
        "streamer_nickname": ["타비", "따비", "땁이"],
        "streamer_info": ["이세계에서 온 16세 탐험가라는 컨셉의 버튜버"],
        "fan_nickname": ["뿡댕이", "뿌대이"],
    }
    PRE_CONTEXT_WINDOW = 1
    previous_summary = deque(maxlen=PRE_CONTEXT_WINDOW)
    prefix = time.strftime("%Y%m%d_%H%M%S")
    if not os.path.exists(summary_filename_gemini.format(prefix=prefix)):
        with open(summary_filename_gemini.format(prefix=prefix), "w") as f:
            json.dump({"short_term_summary": {}}, f, ensure_ascii=False, indent=4)

    now = 0
    os.environ["GEMINI_API_KEY"] = "AIzaSyDV6QD8CEmuonzjAJWVgOfCdKsLJZeCQ68"

    for context_list in _group_by_time_interval(context_file):
        if context_list:
            context_prompt = _get_context_prompt(context_list)
            response = llm_client.request_completion_summary(
                user_api_key="sk-1234",
                metadata=metadata,
                prev_summary="".join(summary for summary in previous_summary),
                cur_context=context_prompt,
            )
            previous_summary.append(response)

            with open(summary_filename_gemini.format(prefix=prefix), encoding="utf-8") as f:
                summaries = json.load(f)
            short_term_summary = summaries["short_term_summary"]
            short_term_summary[now] = response
            summaries["short_term_summary"] = short_term_summary
            with open(summary_filename_gemini.format(prefix=prefix), "w", encoding="utf-8") as f:
                json.dump(summaries, f, ensure_ascii=False, indent=4)

            print(f"{now}min ~ {now + 2}min", "=" * 30)
            now += 2
            print(response)
