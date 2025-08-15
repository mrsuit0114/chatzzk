from dotenv import load_dotenv

from core import schemas
from llm_tasks import LLMTask

PROMPT_BUILDER_TYPE = "langfuse"
LLM_CLIENT_TYPE = "litellm"
TASK_DATA = schemas.ShortTermSummaryData(request="세계에서 가장 인구가 적은 나라는 어디인가요?")

load_dotenv("./LLMService/.env")


def main():
    llm_task = LLMTask(PROMPT_BUILDER_TYPE, LLM_CLIENT_TYPE)

    res = llm_task.short_term_summary(TASK_DATA)
    print(res)


main()
