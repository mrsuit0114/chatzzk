import requests

HEADERS = {"User-Agent": ""}


def fetch_chatChannelId(channel_id: str) -> str:
    url = f"https://api.chzzk.naver.com/polling/v2/channels/{channel_id}/live-status"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        response = response.json()

        chatChannelId = response["content"]["chatChannelId"]
        # liveOn = response["content"]["status"]  "OPEN" or "CLOSE"
        assert chatChannelId is not None
        return chatChannelId
    except Exception as e:
        raise e


def fetch_channelName(channel_id: str) -> str:
    url = f"https://api.chzzk.naver.com/service/v1/channels/{channel_id}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        response = response.json()
        return response["content"]["channelName"]
    except Exception as e:
        raise e


def fetch_accessToken(chat_channel_id: str) -> tuple:
    url = f"https://comm-api.game.naver.com/nng_main/v1/chats/access-token?channelId={chat_channel_id}&chatType=STREAMING"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        response = response.json()
        return response["content"]["accessToken"], response["content"]["extraToken"]
    except Exception as e:
        raise e


def fetch_userIdHash() -> str:
    url = "https://comm-api.game.naver.com/nng_main/v1/user/getUserStatus"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        response = response.json()
        return response["content"]["userIdHash"]  # null
    except Exception as e:
        raise e
