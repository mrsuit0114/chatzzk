from pydantic import BaseModel


class Metadata(BaseModel):
    category: str
    streamer_name: str
    streamer_nickname: list[str]
    streamer_info: list[str]
    fan_nickname: list[str]

    def to_dict(self):
        result = {}
        for field, value in self.__dict__.items():
            if isinstance(value, list):
                # 각 원소를 '로 감싸고 ,로 join
                result[field] = ",".join(f"'{v}'" for v in value)
            else:
                result[field] = value
        return result


class ShortTermSummaryParams(BaseModel):
    metadata: Metadata
    prev_summary: str
    cur_context: str


class GeneralParams(BaseModel):
    metadata: Metadata
    prev_summary: str
    cur_context: str
    consideration: str
    request_emphasis: str


class GeneralChoiceParams(BaseModel):
    metadata: Metadata
    prev_summary: str
    cur_context: str
    consideration: str
    request_emphasis: str
