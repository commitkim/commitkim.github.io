# AI News Summariser 🤖

**매일 아침, 경제 뉴스를 AI가 요약해줍니다.**
*This project is generated and maintained by Google's Agentic AI.*

---

## 📝 개요
유튜브 채널(한국경제신문)의 '모닝루틴' 라이브 영상을 텍스트로 변환하고, **Google Gemini**를 사용하여 핵심 내용, 시장 동향, 인사이트를 요약합니다. 요약된 내용은 카카오톡으로 전송되며, 웹사이트에도 게시됩니다.

## ⚙️ 주요 기능
1.  **자동 수집**: YouTube RSS 피드를 모니터링하여 최신 '모닝루틴' 영상을 감지합니다.
2.  **자막 추출**: `youtube-transcript-api`를 사용하여 영상의 자막을 추출합니다.
3.  **AI 요약**: Gemini 2.0 Flash 모델이 자막을 분석하여 구조화된 요약(JSON)을 생성합니다.
4.  **카카오톡 전송**: 요약된 내용을 보기 좋게 포맷팅하여 카카오톡 '나에게 보내기'로 전송합니다.
5.  **웹 리포트**: 상세 분석 내용을 마크다운 형태로 저장하고 대시보드 사이트에 통합합니다.

## 🛠️ 기술 스택
- **Language**: Python 3.12+ (venv)
- **AI Model**: Google Gemini 2.0 Flash
- **APIs**: YouTube Data API (RSS), KakaoTalk REST API
- **Scheduling**: Windows Task Scheduler

## 🧪 테스트
- **Mock 테스트**: 외부 API 호출 없이 로직을 검증합니다.
    ```bash
    ..\tests\test_summariser.bat
    ```
- **Live 테스트**: 실제 API를 호출하여 전체 파이프라인을 검증합니다.
    ```bash
    ..\tests\test_live.bat
    ```

## ⚠️ 주의사항
- **API Quota**: Gemini API 및 YouTube 수집량에 제한이 있을 수 있습니다.
- **Kakao Token**: 카카오톡 토큰은 만료될 수 있으며, `kakao_auth.py`로 갱신이 필요할 수 있습니다.
