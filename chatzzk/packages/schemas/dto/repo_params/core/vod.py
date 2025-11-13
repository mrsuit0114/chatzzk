from typing import TypeAlias

from chatzzk.packages.schemas.dto.repo_params.chzzk.vod import ChzzkVODCreateParams, ChzzkVODFindParams

VODCreateParams: TypeAlias = ChzzkVODCreateParams  # | YoutubeChannelCreateParams
VODFindParams: TypeAlias = ChzzkVODFindParams
