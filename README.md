# Chatzzk
네이버의 인터넷 스트리밍 방송 플랫폼 Chzzk의 채팅내역과 오디오 데이터를 text로 전사한 데이터를 활용해 방송의 context를 구성하고 LLM을 사용한 부가 가치 생성(요약 생성, 방송 보조, 채팅 추천 등)과 분석 및 시각화 툴을 사용한 피드백 제공, 하이라이트 구간 추출 등 LLM과 인터넷 방송 플랫폼을 접목시켜 다양한 가능성을 시도하는 프로젝트 Chatzzk입니다.


## Technologies Used

- **[WhisperX](https://github.com/m-bain/whisperX)** - ASR (Speech recognition)
- **[Silero VAD](https://github.com/snakers4/silero-vad)** - Voice Activity Detection
- **[ChzzkChat](https://github.com/Buddha7771/ChzzkChat)** - Chat crawler

## 리팩토링 진행 중
예상 프로젝트 구조
```
 .
├──  analysis  
├──  chatzzk
│   ├──  packages
│   │   ├──  constants
│   │   ├──  data_access
│   │   ├──  media_processing
│   │   ├──  ml_clients
│   │   ├──  schemas
│   │   └──  utils
│   └──  services
│       ├──  asr_inference_server
│       ├──  collector
│       └──  llm_service
├──  docker-compose.yml
├──  litellm_proxy
├──  makefile
├──  minio
├──  poetry.lock
├──  pyproject.toml
├──  README.md
└──  scripts
    ├──  Dockerfile
    ├──  init_db.py
    └── 󰌠 requirements.txt
```
