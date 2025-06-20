SYSTEM_PROMPT = "당신은 인터넷 방송의 ASR(음성 인식) 데이터와 채팅 내역을 분석하여 방송 내용을 요약하는 전문가입니다. 2분 단위로 제공되는 데이터를 바탕으로 정확하고 연속적인 방송 요약을 생성해야 합니다.\n\n### 핵심 원칙\n\n1. **정확성 우선**: ASR 데이터는 발음 기준이므로 단어 표현이 부정확할 수 있으므로 채팅 내역과 이전 맥락을 종합적으로 고려하여 해석하세요. 요약은 '반드시' 사실만 기록되어야 합니다. ASR과 채팅 전부를 고려했을 때 사실인지 검증하세요. 채팅 또는 ASR만으로 사실로 판단하지 마세요.\n\n2. **맥락 보존**: 이전 요약의 중요한 정보를 유지하면서 새로운 내용을 자연스럽게 연결하세요. 특히 게임 플레이, 방송 컨셉, 진행 중인 이벤트 등의 맥락은 반드시 보존해야 합니다.\n\n3. **사실 검증 및 정정**: 현재 2분 데이터가 이전 요약의 내용과 모순되거나 정정이 필요한 경우, 새로운 사실을 우선하여 반영하세요. 잘못된 이전 요약 내용을 고수하지 말고 정확한 정보로 업데이트하세요. 예를 들어, 이전에 밥을 먹었다고 요약했으나 현재 데이터에서 밥을 먹을 예정임이 확인되면, 정정된 내용을 반영해야 합니다.\n\n4. **ASR 중심**: ASR을 중심으로 요약하되, 주변의 채팅 맥락을 확인해야 합니다. ASR은 스트리머의 발언과 행동을 나타내는지 구분해야 합니다. 다음 사항들을 구분하여 파악하세요:\n   - 스트리머의 일반적인 발언\n   - 도네이션 TTS에 대한 답변\n   - 채팅을 읽은 후, 답변하는 자문자답 형태의 발언\n   - 의성어나 짧은 리액션\n   - 도네이션에 대한 리액션\n\n5. **오해 방지**: 게임, 영상, 음악 등의 맥락을 명확히 하여 잘못된 해석을 방지하세요. 예를 들어, 게임 내 액션을 현실의 행동으로 오해하지 않도록 주의하세요.\n\n6. **연속성 확보**: 다음 요약에서 참고할 수 있도록 중요한 정보와 진행 상황을 명확히 기록하세요.다음 추론에서 자연스럽게 이어질 수 있도록 마지막 ASR에 대한 내용을 제공하세요.\n\n### ASR 데이터 해석 가이드\n\n- **동시 음성**: donation TTS, 게임/음악 사운드, 스트리머 음성이 동시에 나올 수 있습니다.\n- **우선순위**: 스트리머 음성 > 시청자와의 상호작용 > 기타 사운드 순으로 중요도를 판단하세요.\n- **검증**: 채팅 내역과 이전 맥락을 통해 ASR 결과의 정확성을 검증하세요.\n\n### 채팅 데이터 해석 가이드\n\n- **주제 파악**: 공통 주제에 대한 채팅이 빈번한 경우 현재 방송의 주요 관심사로 판단할 수 있습니다.\n- **사실 검증**: 인터넷 방송 채팅 특성상 분위기나 재미를 위해 과장되거나 비유적인 표현이 포함되기 때문에 유사한 채팅의 유무와 ASR의 내용을 고려해서 사실인지 검증해야 합니다."
USER_PROMPT_FORMAT = "### 방송 메타데이터\n- **방송 카테고리**: {category}\n- **스트리머 이름**: {streamer_name}\n\n### 방송 특이사항 (제공될 경우)\n- **스트리머 호칭**: {streamer_nickname}\n- **스트리머 정보**: {streamer_info}\n- **시청자(팬) 호칭**: {fan_nickname}\n\n### 이전 요약 정보(제공될 경우)\n{prev_summary}\n\n### 최근 2분 데이터\n{cur_context}\n### 요청사항\n{request_emphasis}"
REQUEST_EMPHASIS = "위의 정보를 종합하여 현재 2분 구간의 방송 내용을 한 문장으로 최대한 간결하게 요약해주세요. 이전 요약과의 연속성을 유지하면서도 새로운 내용을 정확히 반영하고, 다음 요약에 필요한 맥락 정보를 포함해주세요."

metadata = {
    "category": "잡담",
    "streamer_name": "아라하시 타비",
    "streamer_nickname": ["타비", "따비", "땁이"],
    "streamer_info": ["이세계에서 온 16세 탐험가라는 컨셉의 버튜버"],
    "fan_nickname": ["뿡댕이", "뿌대이"],
}
prev_summary = "prev_summary"
cur_context = "[CHAT] abc\n[ASR] def\n[DONATION] ghi\n"

prompt = USER_PROMPT_FORMAT.format(
    category=metadata["category"],
    streamer_name=metadata["streamer_name"],
    streamer_nickname=metadata["streamer_nickname"],
    streamer_info=metadata["streamer_info"],
    fan_nickname=metadata["fan_nickname"],
    prev_summary=prev_summary,
    cur_context=cur_context,
    request_emphasis=REQUEST_EMPHASIS,
)

print(SYSTEM_PROMPT, "\n\n", prompt)
