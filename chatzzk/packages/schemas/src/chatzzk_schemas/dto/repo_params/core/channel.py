from typing import TypeAlias

from chatzzk_schemas.dto.repo_params.chzzk.channel import ChzzkChannelCreateParams, ChzzkChannelFindParams

ChannelCreateParams: TypeAlias = ChzzkChannelCreateParams  # | YoutubeChannelCreateParams
ChannelFindParams: TypeAlias = ChzzkChannelFindParams
