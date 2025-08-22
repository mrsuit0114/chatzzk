import os

# 타입 코드 정의
TYPE_CODES = {100: "채팅", 1000: "후원", 10000: "ASR"}


def format_duration(ms):
    """밀리초를 시:분:초 형식으로 변환"""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_file_id(filename):
    """파일명에서 숫자 ID 추출"""
    try:
        return os.path.splitext(filename)[0]
    except Exception:
        return None
