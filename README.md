# Chatzzk
네이버의 인터넷 스트리밍 방송 플랫폼 Chzzk의 채팅내역과 오디오 데이터를 text로 전사한 데이터로 방송의 context를 구성하고 LLM과 분석 및 시각화 툴을 사용해 다양한 가능성을 점검하는 프로젝트 Chatzzk입니다.


## Technologies Used

### English
- **[WhisperX](https://github.com/m-bain/whisperX)** - ASR (Speech recognition)
  - License: BSD-2-Clause
- **[Silero VAD](https://github.com/snakers4/silero-vad)** - Voice Activity Detection
  - License: MIT
- **[ChzzkChat](https://github.com/Buddha7771/ChzzkChat)** - Chat crawler
  - Based on the work of [Buddha7771](https://github.com/Buddha7771)

### Usage
#### MonitorWorker
```bash
docker build -t monitor-worker ./MonitorWorker
docker run --rm --gpus all --name {container_name} -e CHANNEL_ID={치지직 방송 채널 ID} -v "$(pwd)/MonitorWorker/whisperx_models:/app/whisperx_models" monitor-worker
```

### Issue
개인 데스크탑에서 원인을 알 수 없는 치명적 시간 측정 이슈 발생 - time.time()을 신뢰할 수 없고 실시간 모니터링의 성능에 영향을 미침
https://www.notion.so/context-feat-23aad172fa2180329879ca6e2b67c871?source=copy_link
