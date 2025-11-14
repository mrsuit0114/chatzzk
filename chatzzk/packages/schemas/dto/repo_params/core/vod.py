from typing import TypeAlias

from chatzzk.packages.constants.service_codes import PlatformCode
from chatzzk.packages.schemas.dto.repo_params.chzzk.vod import ChzzkVODCreateParams, ChzzkVODFindParams

VODCreateParams: TypeAlias = ChzzkVODCreateParams  # | YoutubeChannelCreateParams
VODFindParams: TypeAlias = ChzzkVODFindParams


def get_vod_find_params(platform_code: PlatformCode, **kwargs) -> VODFindParams:
    match platform_code:
        case PlatformCode.CHZZK:
            return ChzzkVODFindParams(**kwargs)
