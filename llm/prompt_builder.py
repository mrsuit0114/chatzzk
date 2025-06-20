from data_types.context_data import ContextData


class PromptBuilder:
    def __init__(self, config: dict):
        self.system_prompt = config["system_prompt"]
        self.user_prompt_format = config["user_prompt_format"]
        self.request_emphasis = config["request_emphasis"]

    def build_prompt_for_choices(
        self,
        request_type: str,
        metadata: dict[str, str],
        prev_summary: str,
        cur_context: list[ContextData],
        custom_request: str,
    ) -> list[dict[str, str]]:
        system_prompt = self.system_prompt[request_type]
        request_emphasis = self.request_emphasis[request_type]
        user_prompt = self.user_prompt_format.format(
            metadata, prev_summary, cur_context, custom_request, request_emphasis
        )
        return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

    def build_prompt_for_summary(
        self,
        metadata: dict,  # category, streamer_name, streamer_nickname, streamer_info, fan_nickname
        prev_summary: str,
        cur_context: str,
    ) -> list[dict[str, str]]:
        category = metadata["category"]
        streamer_name = metadata["streamer_name"]
        streamer_nickname = ". ".join(f"'{nickname}'" for nickname in metadata["streamer_nickname"])
        streamer_info = ", ".join(metadata["streamer_info"])
        fan_nickname = ", ".join(f"'{nickname}'" for nickname in metadata["fan_nickname"])
        system_prompt = self.system_prompt["summary"]
        request_emphasis = self.request_emphasis["summary"]
        user_prompt = self.user_prompt_format.format(
            category=category,
            streamer_name=streamer_name,
            streamer_nickname=streamer_nickname,
            streamer_info=streamer_info,
            fan_nickname=fan_nickname,
            prev_summary=prev_summary,
            cur_context=cur_context,
            request_emphasis=request_emphasis,
        )
        return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
