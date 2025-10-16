from chatzzk.packages.clients.chzzk.chzzk_api_client import ChzzkApiClient
from chatzzk.packages.data_access.repositories.channel import ChannelRepository
from chatzzk.packages.data_access.repositories.vod import VodRepository


class ChzzkCollectorService:
    def __init__(
        self,
        chzzk_api_client: ChzzkApiClient,
        channel_repo: ChannelRepository,
        vod_repo: VodRepository,
    ):
        self.api_client = chzzk_api_client
        self.channel_repo = channel_repo
        self.vod_repo = vod_repo
