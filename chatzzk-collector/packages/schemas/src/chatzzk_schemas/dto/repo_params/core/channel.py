from typing import TypeAlias

from chatzzk_constants.service_codes import PlatformCode
from chatzzk_schemas.dto.repo_params.chzzk.channel import ChzzkChannelCreateParams, ChzzkChannelFindParams

ChannelCreateParams: TypeAlias = ChzzkChannelCreateParams  # | YoutubeChannelCreateParams
ChannelFindParams: TypeAlias = ChzzkChannelFindParams


def get_channel_find_params(platform_code: PlatformCode, **kwargs) -> ChannelFindParams:
    match platform_code:
        case PlatformCode.CHZZK:
            return ChzzkChannelFindParams(**kwargs)
