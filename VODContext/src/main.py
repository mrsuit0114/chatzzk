import json
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from streamlink import Streamlink
from tqdm import tqdm


class ChzzkStreamExtractor:
    VOD_URL = "https://apis.naver.com/neonplayer/vodplay/v2/playback/{video_id}?key={in_key}"
    VOD_INFO = "https://api.chzzk.naver.com/service/v2/videos/{video_no}"
    OUTPUT_DIR = "data/videos"

    @staticmethod
    def extract_streams(link):
        # Initialize Streamlink session
        session = Streamlink()

        # Match the link to extract necessary information
        match = re.match(r"https?://chzzk\.naver\.com/(?:video/(?P<video_no>\d+)|live/(?P<channel_id>[^/?]+))$", link)
        if not match:
            print("Invalid link\n")
            return

        video_no = match.group("video_no")

        return ChzzkStreamExtractor._get_vod_streams(session, video_no)

    @staticmethod
    def download_video(video_url, output_path):
        session = requests.Session()

        # 파일 크기를 얻기 위한 초기 요청
        with session.get(video_url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))

        if total_size == 0:
            print("Failed to get file size. Aborting download.")
            return

        part_size = 1024 * 1024 * 10
        parts = total_size // part_size + (1 if total_size % part_size else 0)

        tqdm_bar = tqdm(total=total_size, unit="B", unit_scale=True, desc="Downloading")

        # 다운로드된 조각 데이터를 임시로 저장할 딕셔너리
        parts_data = {}

        def download_part(part):
            start = part * part_size
            end = start + part_size - 1 if (start + part_size - 1) < total_size else total_size
            headers = {"Range": f"bytes={start}-{end}"}
            with session.get(video_url, headers=headers, stream=True) as r:
                r.raise_for_status()
                return r.content

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_part = {executor.submit(download_part, part): part for part in range(parts)}

            for future in as_completed(future_to_part):
                part_data = future.result()
                part_number = future_to_part[future]

                # 다운로드된 조각을 순서에 맞게 임시 저장
                parts_data[part_number] = part_data
                tqdm_bar.update(len(part_data))

        tqdm_bar.close()

        # 모든 조각 다운로드 완료 후, 원래 순서대로 파일에 쓰기
        print("Combining downloaded parts...")
        with open(output_path, "wb") as file:
            for part_number in range(parts):
                file.write(parts_data[part_number])

        print("Download completed!\n")

    @staticmethod
    def _print_dash_manifest(video_url):
        try:
            response = requests.get(video_url, headers={"Accept": "application/dash+xml"})
            response.raise_for_status()

            root = ET.fromstring(response.text)
            ns = {"mpd": "urn:mpeg:dash:schema:mpd:2011", "nvod": "urn:naver:vod:2020"}

            reps = []
            for rep in root.findall(".//mpd:Representation", namespaces=ns):
                width = rep.get("width")
                height = rep.get("height")
                resolution = min(int(width), int(height))
                base_url = rep.find(".//mpd:BaseURL", namespaces=ns).text
                if base_url.endswith("/hls/"):
                    continue
                reps.append([resolution, base_url])

            # 해상도(x[0])를 기준으로 오름차순 정렬
            sorted_reps = sorted(reps, key=lambda x: x[0])

            low_resolution_url = sorted_reps[0][1]  # only need for extracting wav, not important resolution

            return low_resolution_url
        except requests.RequestException as e:
            print("Failed to fetch DASH manifest:", str(e), "\n")
        except ET.ParseError as e:
            print("Failed to parse DASH manifest XML:", str(e), "\n")

    @staticmethod
    def _get_vod_streams(session, video_no):
        api_url = ChzzkStreamExtractor.VOD_INFO.format(video_no=video_no)

        UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        try:
            response = requests.get(api_url, headers={"User-Agent": UserAgent})
            response.raise_for_status()
        except requests.RequestException as e:
            print("Failed to fetch video information:", str(e), "\n")
            return

        if response.status_code == 404:
            print("Video not found\n")
            return

        try:
            content = response.json().get("content", {})
            video_id = content.get("videoId")
            in_key = content.get("inKey")

            if video_id is None or in_key is None:
                print("This is a need to login video.", "\n")
                cookies = ChzzkStreamExtractor._load_cookies_from_file("cookies.json")
                if cookies is not None:
                    # Retry the request with cookies
                    response = requests.get(api_url, cookies=cookies, headers={"User-Agent": UserAgent})
                    response.raise_for_status()

                    # Update video_id and in_key with the new values
                    content = response.json().get("content", {})
                    video_id = content.get("videoId")
                    in_key = content.get("inKey")

            video_url = ChzzkStreamExtractor.VOD_URL.format(video_id=video_id, in_key=in_key)

            author = content.get("channel", {}).get("channelName")
            category = content.get("videoCategory")
            title = content.get("videoTitle")

            print(f"Author: {author}, Title: {title}, Category: {category}")

            base_url = ChzzkStreamExtractor._print_dash_manifest(video_url)

            if base_url:
                output_path = f"{ChzzkStreamExtractor.OUTPUT_DIR}/{video_no}.mp4"

                ChzzkStreamExtractor.download_video(base_url, output_path)

        except json.JSONDecodeError as e:
            print("Failed to decode JSON response:", str(e))

    @staticmethod
    def _load_cookies_from_file(file_path):
        try:
            with open(file_path) as file:
                cookies = json.load(file)
            return cookies
        except FileNotFoundError:
            print(f"Cookie file not found: {file_path}", "\n")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {file_path}", "\n")
            return None

    @staticmethod
    def clean_filename(filename):
        cleaned_filename = re.sub(
            r"[♥♡ღ⭐㉦✧》《♠♦❤️♣✿ꈍᴗ\/@!~*\[\]\#\$\%\^\&\(\)\-\_\=\+\<\>\?\;\:\'\"]", "", filename
        )
        return cleaned_filename


if __name__ == "__main__":
    while True:
        link = input("Enter the link (or type 'exit' to quit): ")

        if link.lower() == "exit":
            break

        ChzzkStreamExtractor.extract_streams(link)
