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

### data example
full_context.jsonl
```bash
{"timestamp_ms": 295959, "content": "안녕하세요", "type_code": 100, "prompt_str": "[CHAT] 안녕하세요\n"}
{"timestamp_ms": 296071, "content": "굿", "type_code": 100, "prompt_str": "[CHAT] 굿\n"}
{"timestamp_ms": 296109, "content": "ㅋㅋ", "type_code": 100, "prompt_str": "[CHAT] ㅋㅋ\n"}
{"timestamp_ms": 297877, "content": "네", "type_code": 100, "prompt_str": "[CHAT] 네\n"}
{"timestamp_ms": 298096, "content": "인터넷을 하루 맨종일 하면서", "type_code": 10000, "prompt_str": "[ASR] 인터넷을 하루 맨종일 하면서\n"}
{"timestamp_ms": 300169, "content": "그랬군요", "type_code": 100, "prompt_str": "[CHAT] 그랬군요\n"}
{"timestamp_ms": 300256, "content": "면.", "type_code": 10000, "prompt_str": "[ASR] 면.\n"}
{"timestamp_ms": 301220, "content": "ㅔㅔ", "type_code": 100, "prompt_str": "[CHAT] ㅔㅔ\n"}
```
summary.json
```bash
{
  "short_term_summary": {
    "120": "summary1",
    "240": "summary2",
    "360": "summary3",
    "480": "summary4",
    ...
    },
  "middle_term_summary":{}
}
```
