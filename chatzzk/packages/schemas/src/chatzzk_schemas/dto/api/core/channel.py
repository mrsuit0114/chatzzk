# channel_llm_metadata와 result_object_keys는 어디서 관리하는게 적절할까?
# channel_llm_metadata는 채널에 종속적이므로 채널에서 관리하는 것이 일반적일 것
# result_object_keys는 vod에 종속되기 때문에 vod 관리에서 담당해야할 것
from typing import TypeAlias

from chatzzk_schemas.dto.api.chzzk.channel import ChzzkChannelAddRequestDTO, ChzzkChannelAddResponseDTO

# from chatzzk_schemas.dto.youtube.channel import YoutubeChannelCreateDTO

# 채널 생성에 사용될 수 있는 모든 DTO 타입을 묶어 별칭으로 정의
ChannelAddRequestDTO: TypeAlias = ChzzkChannelAddRequestDTO  # | YoutubeChannelCreateDTO
ChannelAddResponseDTO: TypeAlias = ChzzkChannelAddResponseDTO
