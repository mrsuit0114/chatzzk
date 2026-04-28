## 🎯 Project Overview: CHATZZK (1-Minute Summary)

> **"방송 흐름을 보존하는 멀티모달 데이터 분석 파이프라인 및 웹 서비스"**
> 단순 스크립트 요약을 넘어 오디오(ASR)와 시청자 반응 지표를 시간 축으로 결합하여 맥락 있는 요약을 제공합니다.

### 🛠 Core Engineering & Decisions
- **AI/ML**: ASR 모델 평가 체계 구축 및 **Rule-based 정제로 환각 23% 제거**
- **Pipeline**: Prefect 기반 **내결함성(Checkpoint)**을 갖춘 데이터 오케스트레이션 설계
- **Optimization**: 계층형 컨텍스트 재설계로 **LLM 토큰 소모량 25% 절감**
- **Infrastructure**: GPU/CPU 리소스 분리 및 Cloudflare를 활용한 **비용 효율적 배포**

### 👤 Role (1-Person Project)
- 데이터 파이프라인 E2E 설계 및 구축
- 모델 평가/선정 및 전후처리 로직 구현
- 프롬프트/컨텍스트 엔지니어링
- React 기반 분석 대시보드 웹 서비스 개발
