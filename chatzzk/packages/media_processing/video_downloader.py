# packages/utils/downloader.py

from pathlib import Path

import requests
from loguru import logger

# tqdm은 선택적 의존성이므로, 설치되지 않았을 때를 대비
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


def download_file_from_url(
    url: str,
    destination_path: str | Path,
    session: requests.Session | None = None,
    show_progress: bool = True,
) -> None:
    """
    주어진 URL에서 파일을 스트리밍 방식으로 다운로드하여 지정된 경로에 저장합니다.
    tqdm을 사용하여 진행률을 표시할 수 있습니다.
    # TODO: http range를 사용해서 병렬로 다운로드할 수 있도록 구성할 것

    Args:
        url (str): 다운로드할 파일의 URL.
        destination_path (str | Path): 파일이 저장될 경로.
        session (Optional[requests.Session], optional): 재사용할 requests 세션.
        show_progress (bool, optional): 진행률 표시줄을 보여줄지 여부.
    """
    logger.info(f"📥 Starting download from URL: {url}")
    _session = session or requests.Session()
    dest_path = Path(destination_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)  # 디렉토리 생성 책임도 포함

    try:
        with _session.get(url, stream=True, timeout=300) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))

            with open(dest_path, "wb") as f:
                # tqdm이 설치되어 있고, show_progress가 True일 때만 진행률 표시
                if tqdm and show_progress:
                    with tqdm(total=total_size, unit="B", unit_scale=True, desc=dest_path.name) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))
                else:  # tqdm이 없거나 원하지 않을 경우
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

        logger.success(f"✅ Download complete: {dest_path}")

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Download failed for {url}: {e}")
        if dest_path.exists():
            dest_path.unlink()  # 실패 시 부분 파일 삭제
        raise ConnectionError(f"Failed to download from {url}") from e
