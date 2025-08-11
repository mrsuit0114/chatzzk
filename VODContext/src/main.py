import sys

from config import Config
from vod_context_fetcher import VodContextFetcher


def main():
    try:
        config = Config()  # 클래스 인스턴스 생성
        vod_context_fetcher = VodContextFetcher(config)

        while True:
            try:
                video_no_or_url = input("Enter video_num or '@<mp4_url>' (or type 'q' to exit): ")

                if video_no_or_url.lower() == "q":
                    break

                # 숫자 입력일 경우 기존 플로우
                if video_no_or_url.isdigit():
                    vod_context_fetcher.run(int(video_no_or_url))
                    continue

                # URL 입력(@로 시작 가능)
                mp4_url = video_no_or_url.lstrip("@").strip()
                if mp4_url.startswith("http") and ".mp4" in mp4_url:
                    # output_path용 video_no 추가 입력
                    save_video_no = input("Enter video_num to use as output filename (digits only): ")
                    if not save_video_no.isdigit():
                        print("❌ Please enter a valid video number (digits only)")
                        continue

                    # 우선 다운로드만 수행 (Step1 스킵 유도)
                    extractor = vod_context_fetcher.chzzk_stream_extractor
                    ok = extractor.download_from_direct_url(mp4_url, int(save_video_no))
                    if not ok:
                        print("❌ Failed to download from direct URL")
                        continue

                    # 나머지 파이프라인 진행 (이미 mp4가 있으면 Step1 스킵)
                    vod_context_fetcher.run(int(save_video_no))
                    continue

                print("❌ Please enter a valid video number or a valid mp4 URL (optionally prefixed with '@')")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error processing input {video_no_or_url}: {e}")
                continue

    except Exception as e:
        print(f"❌ Failed to initialize application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
