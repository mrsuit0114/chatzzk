# llm_client를 활용해 다양한 기능을 수행 - vod를 기준으로 요약 생성, choice, general, 실시간까지
# API과 통신하는 부분이며 LLM API에 대한 비동기 수행


from itertools import groupby

from loguru import logger
from tqdm import tqdm

from data_types.context_data import ContextData
from data_types.task_param import ShortTermSummaryParams
from llm.llm_client import LLMClientFactory


def _get_context_prompt(context_list: list[ContextData]) -> str:
    # vod 용도
    context = ""
    for ele in context_list:
        context += ele.prompt_str
    return context


class CompletionManager:
    # 추후에 API서버에서 배치단위로 와서 비동기로도 수행되도록 구성 필요
    def __init__(self, proxy_url: str, config: dict):
        self.proxy_url = proxy_url
        self.llm_clients = {k: LLMClientFactory.create_llm_client(config[k], k, proxy_url) for k in config.keys()}

    def _summarize_by_short_term(self, api_key: str, params: ShortTermSummaryParams) -> str:
        result = self.llm_clients["short_term_summary"].complete(api_key, params)
        return result

    # vod처럼 full_context를 전부 알고 있을 때 사용
    def summarize_by_short_term_of_full_context(
        self,
        api_key: str,
        full_context: list[ContextData],
        params: ShortTermSummaryParams,
        context_interval_s: int,
    ) -> list[str]:
        summaries = []
        for _, group in tqdm(
            groupby(full_context, key=lambda x: x.timestamp_ms // (context_interval_s * 1000)),
            desc="Short-term summarization",
        ):
            try:
                params.cur_context = _get_context_prompt(list(group))
                cur_summary = self._summarize_by_short_term(api_key, params)
                summaries.append(cur_summary)
                params.prev_summary = cur_summary
            except Exception as e:
                # 예외 발생 시 지금까지의 summaries를 반환
                logger.error(f"generate summary error!{e}")
                break
        return summaries
