# Chatzzk
A real-time audio-driven text generation framework for live streams, capable of understanding the flow of broadcasts and generating context-aware responses from user prompts.


## Technologies Used

### English
- **[WhisperX](https://github.com/m-bain/whisperX)** - ASR (Speech recognition)
  - License: BSD-2-Clause
- **[Silero VAD](https://github.com/snakers4/silero-vad)** - Voice Activity Detection
  - License: MIT
- **[ChzzkChat](https://github.com/Buddha7771/ChzzkChat)** - Chat crawler
  - Based on the work of [Buddha7771](https://github.com/Buddha7771)

### 한국어
- [WhisperX](https://github.com/m-bain/whisperX) - ASR
  - 라이센스: BSD-2-Clause License
- [Silero VAD](https://github.com/snakers4/silero-vad) - 음성 활동 감지
  - 라이센스: MIT License
- [ChzzkChat](https://github.com/Buddha7771/ChzzkChat) - 채팅 크롤링 구현
  - [Buddha7771](https://github.com/Buddha7771)님의 작업을 기반으로 함

## Installation & Setup

### English
1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install CUDA dependencies
```bash
sudo apt install libcudnn8
```

3. Run the application:
```bash
python main.py
```

### 한국어
1. Python 의존성 설치:
```bash
pip install -r requirements.txt
```

2. CUDA 의존성 설치:
```bash
sudo apt install libcudnn8
```

3. 애플리케이션 실행:
```bash
python main.py
```

## 🚧 Project Status

### ✅ Completed

- Real-time data pipeline established for live streams.
- Synchronized audio (ASR) and chat data collection implemented.
- Built contextual representation combining chat messages and transcribed audio.

### 🛠️ In Progress / Upcoming

- Periodic analysis of broadcast flow to detect transitions and context shifts.
- Text generation module:
  - Generates responses based on real-time context (chat + ASR).
  - Adapts to user prompts and the ongoing flow of the broadcast.
  - Supports use cases like chat recommendation, summarization, and content generation.
