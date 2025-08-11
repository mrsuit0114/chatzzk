# VOD Context Project

특정 방송 플랫폼의 VOD를 저장, WAV로 추출, VAD 및 ASR 수행, 채팅 내역 크롤링을 수행하고 하나의 방송 full_context를 구성하는 모듈입니다다.

## 🚀 주요 기능

- **VOD 다운로드**: Chzzk 플랫폼의 VOD 스트림 추출 및 다운로드
- **오디오 처리**: MP4에서 WAV 추출 및 음성 활동 감지(VAD)
- **음성 인식**: WhisperX를 사용한 한국어 ASR
- **채팅 크롤링**: 실시간 채팅 내역 수집
- **컨텍스트 병합**: ASR과 채팅 데이터를 시간순으로 병합

## 📋 요구사항

- Python 3.11+
- FFmpeg
- CUDA 지원 GPU (ASR 성능 향상을 위해 권장)

## ⚙️ 설정

### 환경 변수

프로젝트는 환경 변수를 통해 설정을 관리합니다. 주요 설정은 다음과 같습니다:

- **데이터 디렉토리**: `VOD_DATA_DIR`, `VOD_VIDEO_DIR` 등
- **ASR 모델**: `VOD_ASR_MODEL_SIZE`, `VOD_WHISPERX_MODEL_DIR` 등
- **네트워크**: `VOD_MAX_RETRIES`, `VOD_TIMEOUT` 등

## 🎯 사용법

### 기본 사용법

```bash
docker build -t vod-context ./VODContext
docker compose run --rm vod-context

Enter video_num or '@<mp4_url>' (or type 'q' to exit):
# 1234567 or @https:// ~ and 1234567(video_no for output_path)
```

## 📁 프로젝트 구조

```
VODContext/
├── whisperx_models/            # whisperX 모델
├── src/
│   ├── main.py                 # 메인 실행 파일
│   ├── config.py               # 설정 관리
│   ├── vod_context_fetcher.py  # 전체 파이프라인 관리
│   ├── chzzk_stream_extractor.py  # VOD 스트림 추출
│   ├── wav_extractor.py        # WAV 추출
│   ├── audio_processor.py      # 오디오 처리 (VAD + ASR)
│   ├── chzzk_chat_crawler.py   # 채팅 크롤링
│   ├── context_merge_manager.py # 컨텍스트 병합
│   ├── audio/                  # 오디오 처리 모듈
│   │   ├── vad.py             # Voice Activity Detection
│   │   └── asr.py             # Automatic Speech Recognition
│   └── data_types/            # 데이터 타입 정의
│       └── context_data.py    # 컨텍스트 데이터 구조
├── env.example                 # 환경 변수 예시
└── README.md                   # 이 파일
```

## 🔄 처리 단계

1. **스트림 추출**: VOD 스트림 URL 획득 및 다운로드
2. **채팅 크롤링**: 채팅 내역 수집 (병렬 처리)
3. **WAV 추출**: MP4에서 오디오 추출
4. **오디오 처리**: VAD 및 ASR 수행
5. **컨텍스트 병합**: 모든 데이터를 시간순으로 병합

## 📚 참고 및 사용한 프로젝트

- **MP4 다운로드 참고**: [chzzk-vod-downloader](https://github.com/321098123/chzzk-vod-downloader)
- **VAD(Voice Activity Detection)**: [Silero VAD](https://github.com/snakers4/silero-vad)
- **ASR(Automatic Speech Recognition)**: [WhisperX](https://github.com/m-bain/whisperX)
- **MP4 URL 참고**: [chzzk-vod](https://chzzk-vod.streamlit.app) - 같은 영상과 화질에 대해 코드에서 사용하는 url과 웹에서 사용하는 url이 다르며 웹의 url이 안정적이므로 사용을 권장
