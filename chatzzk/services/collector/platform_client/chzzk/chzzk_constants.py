from chatzzk.packages.constants.service_codes import ContextType

CHZZK_MESSAGE_TYPE_CODE_TO_CONTEXT_TYPE: dict[int, ContextType] = {
    1: ContextType.CHAT,
    10: ContextType.DONATION,
    # 11은 구독 메시지, 12는 구독 선물, 30은 시스템 메시지
}

CHZZK_WEBSOCKET_OP_CODES: dict[str, int] = {
    "ping": 0,
    "pong": 10000,
    "connect": 100,
    "send_chat": 3101,
    "request_recent_chat": 5101,
    "chat_message": 93101,
    "donation_message": 93102,
}
