"""
Gemini AI 요약 모듈
- 듀얼 출력: kakao_summary (카톡용 헤드라인) + web_report (웹사이트용 심층 분석)
- 두 요약은 main_topics를 공통 뼈대로 공유하여 내용이 정합됨

Refactored: uses core.config for API key and model settings.
"""

import json
import re

from google import genai

from core.config import Config
from core.logger import get_logger

log = get_logger("news_briefing.summarizer")

# Lazy-initialized client
_client = None


def _get_client():
    global _client
    if _client is None:
        cfg = Config.instance()
        api_key = cfg.get_secret("GEMINI_API_KEY")
        _client = genai.Client(api_key=api_key)
    return _client


# ─────────────────────────────────────────────
# 듀얼 프롬프트: 카카오톡 + 웹 리포트 동시 생성
# ─────────────────────────────────────────────
DUAL_SUMMARY_PROMPT = """
당신은 냉철하고 분석적인 '경제 뉴스 전문 AI 애널리스트'입니다.
제공된 유튜브 경제 영상의 자막을 분석하여, 아래 JSON 스키마에 맞게 요약을 작성하십시오.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[핵심 원칙: 카카오톡 ↔ 웹 리포트 연동]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- `main_topics`가 공통 뼈대입니다.
- `kakao_summary`는 각 main_topic을 한 줄로 요약합니다. (헤드라인 역할)
- `web_report`는 각 main_topic을 상세히 분석합니다. (심층 리포트 역할)
- 두 요약은 반드시 동일한 주제를 다루되, 깊이만 다릅니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[공통 지침]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 감정적 표현 배제, 사실·수치 위주로 명확하게 작성
2. 주가, 환율, 등락폭 등 구체적 수치는 반드시 포함
3. 영상에 없는 내용은 절대 지어내지 말고 null 표기
4. 반드시 유효한 JSON으로만 응답 (```json 코드블록 안에 작성)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[입력 데이터]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 영상 링크: {video_url}
- 자막 내용: {transcript}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[출력 JSON 스키마]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{
    "main_topics": ["주제1", "주제2", "주제3 (최대 5개, 핵심 토픽)"],

    "key_insights": [
        "시장에 영향을 미친 핵심 인과관계 1",
        "주요 경제 정책 또는 기업 이슈 2",
        "향후 전망 또는 리스크 요인 3 (최대 5개)"
    ],

    "kakao_summary": "(아래 규칙 참고)",

    "web_report": "(아래 규칙 참고)"
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[kakao_summary 작성 규칙] — 카카오톡 메시지용 (헤드라인)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- main_topics의 각 주제를 한 줄씩 요약하는 방식으로 작성
- 각 줄은 `▸ [주제명]: 한줄 요약 (핵심 수치 포함)` 형태
- 전체 400자 이내
- 마지막에 💡 한줄 인사이트 추가

예시 형식:
"▸ 미국 CPI 둔화: 시장 예상 하회, 6월 금리인하 기대 강화\\n"
"▸ 반도체 수출 호조: HBM 수요 지속, 삼성·하이닉스 강세\\n"
"▸ 원화 강세: 달러 약세 전환, 외국인 순매수 지속\\n\\n"
"💡 금리인하 기대로 성장주 중심 반등 가능성"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[web_report 작성 규칙] — 웹페이지용 (심층 분석)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Markdown 형식으로 작성 (## 헤더, **, 리스트, 테이블 등 적극 활용)
- 구조:
  1. `## 주요 이슈 분석` — main_topics의 각 주제를 `### 주제명` 형식의 소제목으로 나누어 분석
     - 각 이슈는 **배경** · **영향** · **전망** 3단 구조
  2. `## 💡 투자 인사이트` — 실질적 시사점 2~3가지
  3. `## 📖 용어 해설` — 영상에 나온 전문 용어를 테이블로 설명

- **핵심**: `## 📰 주요 이슈 분석` 섹션의 이슈 제목이 main_topics와 일치해야 합니다.
  kakao_summary에서 한 줄로 요약한 것을 여기서 심층 분석하는 구조입니다.
- kakao_summary보다 3~5배 풍부한 정보량
- 최소 800자 이상 작성
"""


def summarize(transcript, video_id):
    """
    Gemini API를 사용하여 듀얼 요약을 생성합니다.
    503/429 오류 시 최대 3회 재시도 (30s → 60s → 120s).

    Returns:
        dict | None: 요약 JSON 또는 실패 시 None
    """
    import time

    cfg = Config.instance()
    model = cfg.get("ai.model", "gemini-2.5-flash")

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    prompt = DUAL_SUMMARY_PROMPT.format(
        video_url=video_url,
        transcript=transcript
    )

    RETRYABLE_CODES = {429, 503, 500, 502, 504}
    MAX_RETRIES = 3
    BACKOFF_SECONDS = [30, 60, 120]  # 30초 → 60초 → 120초

    for attempt in range(MAX_RETRIES + 1):
        try:
            client = _get_client()
            
            from google.genai import types
            
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=65535,
                )
            )
            text = response.text

            # JSON 추출
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                json_str = json_match.group()

                # 제어 문자 정제 (줄바꿈/탭 보존, 그 외 제거)
                json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', json_str)

                try:
                    result = json.loads(json_str, strict=False)
                except json.JSONDecodeError as e:
                    log.warning(f"1차 JSON 파싱 실패: {e}")
                    try:
                        import ast
                        result = ast.literal_eval(json_str)
                    except Exception as e2:
                        log.error(f"JSON 파싱 실패: {e2}")
                        log.debug(f"원본 텍스트 일부: {text[:200]}...")
                        return None

                # 필수 필드 존재 확인
                if 'kakao_summary' not in result:
                    log.warning("kakao_summary 필드 누락")
                    return None
                if 'web_report' not in result:
                    log.warning("web_report 필드 누락")
                    return None

                log.info(f"듀얼 요약 완료 (카톡: {len(result['kakao_summary'])}자, 웹: {len(result['web_report'])}자)")
                return result

            log.error("JSON 파싱 실패: 응답에서 JSON을 찾을 수 없습니다.")
            try:
                candidates = response.candidates
                if candidates:
                    log.debug(f"Finish Reason: {candidates[0].finish_reason}")
                log.debug(f"Usage Metadata: {response.usage_metadata}")
            except Exception:
                pass
            return None

        except Exception as e:
            err_str = str(e)
            # 재시도 가능한 상태코드인지 확인
            is_retryable = any(str(code) in err_str for code in RETRYABLE_CODES)

            if is_retryable and attempt < MAX_RETRIES:
                wait_sec = BACKOFF_SECONDS[attempt]
                log.warning(
                    f"Gemini API 일시 오류 (시도 {attempt + 1}/{MAX_RETRIES}): {e}\n"
                    f"{wait_sec}초 후 재시도합니다..."
                )
                time.sleep(wait_sec)
            else:
                log.error(f"Gemini 요약 오류 (최종 실패): {e}")
                return None
