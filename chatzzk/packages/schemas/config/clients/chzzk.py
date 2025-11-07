from pydantic import BaseModel

from chatzzk.packages.constants.chzzk import ChzzkAPIConstant


class ChzzkAPIConfig(BaseModel):
    default_headers: dict | None = ChzzkAPIConstant.DEFAULT_HEADERS
    vod_mainfest_headers: dict | None = ChzzkAPIConstant.VOD_MANIFEST_HEADERS

    channel_info_url: str = ChzzkAPIConstant.CHANNEL_INFO_URL
    channel_vods_url: str = ChzzkAPIConstant.CHANNEL_VODS_URL

    vod_info_url: str = ChzzkAPIConstant.VOD_INFO_URL
    vod_chats_url: str = ChzzkAPIConstant.VOD_CHATS_URL
    vod_playback_url: str = ChzzkAPIConstant.VOD_PLAYBACK_URL

    page_size: int = ChzzkAPIConstant.PAGE_SIZE
    worker_num: int = ChzzkAPIConstant.WORKER_NUM
    last_end_ms_offset: int = ChzzkAPIConstant.LAST_END_TIME_OFFSET
    chunk_size: int = ChzzkAPIConstant.CHUNK_SIZE
    rs_idx: int = ChzzkAPIConstant.RS_IDX

    dash_ns: dict = ChzzkAPIConstant.DASH_NS

    proxy: str | None = None
