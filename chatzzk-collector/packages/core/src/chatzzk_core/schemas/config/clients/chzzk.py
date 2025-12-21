from pydantic import BaseModel

from chatzzk_core.constants import ChzzkAPIConstant


class ChzzkAPIConfig(BaseModel):
    default_headers: dict | None = ChzzkAPIConstant.DEFAULT_HEADERS
    vod_mainfest_headers: dict | None = ChzzkAPIConstant.VOD_MANIFEST_HEADERS

    channel_info_url: str = ChzzkAPIConstant.CHANNEL_INFO_URL
    vod_metas_url: str = ChzzkAPIConstant.VOD_METAS_URL

    vod_info_url: str = ChzzkAPIConstant.VOD_INFO_URL
    vod_chats_url: str = ChzzkAPIConstant.VOD_CHATS_URL
    vod_playback_url: str = ChzzkAPIConstant.VOD_PLAYBACK_URL

    page_size: int = ChzzkAPIConstant.PAGE_SIZE
    last_end_ms_offset: int = ChzzkAPIConstant.LAST_END_TIME_OFFSET
    rs_idx: int = ChzzkAPIConstant.RS_IDX

    dash_ns: dict = ChzzkAPIConstant.DASH_NS

    rate_limit_max_rate: int = ChzzkAPIConstant.RATE_LIMIT_MAX_RATE
    rate_limit_time_period: float = ChzzkAPIConstant.RATE_LIMIT_TIME_PERIOD

    proxy: str | None = None
