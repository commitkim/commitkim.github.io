"""
카카오톡 메시지 전송 모듈 (Deduplicated)
- 토큰 관리 (저장, 로드, 갱신)
- 나에게 보내기 API를 통한 메시지 전송
- 초기 인증 설정 (setup)

Refactored: single source of truth for KakaoTalk (was duplicated in Dashboard and Summariser).
Uses core.config for API keys and core.logger for structured logging.
"""

import json
import os
import webbrowser
import requests

from core.config import Config, PROJECT_ROOT
from core.logger import get_logger

log = get_logger("messenger.kakao")


def _get_token_file():
    """Get the path to the kakao_tokens.json file."""
    return os.path.join(PROJECT_ROOT, "kakao_tokens.json")


# ─────────────────────────────────────────────
# 토큰 관리
# ─────────────────────────────────────────────

def _save_tokens(tokens):
    with open(_get_token_file(), "w") as f:
        json.dump(tokens, f)


def _load_tokens():
    try:
        with open(_get_token_file(), "r") as f:
            return json.load(f)
    except Exception:
        return None


def _refresh_token():
    """리프레시 토큰으로 액세스 토큰을 갱신합니다."""
    cfg = Config.instance()
    tokens = _load_tokens()
    if not tokens:
        return None

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        log.error("리프레시 토큰이 없습니다.")
        return None

    api_key = cfg.get_secret("KAKAO_REST_API_KEY")
    client_secret = cfg.get_secret("KAKAO_CLIENT_SECRET")

    data = {
        "grant_type": "refresh_token",
        "client_id": api_key,
        "refresh_token": refresh_token
    }

    if client_secret:
        data["client_secret"] = client_secret

    try:
        response = requests.post("https://kauth.kakao.com/oauth/token", data=data)
        if response.status_code == 200:
            new_tokens = response.json()
            if "refresh_token" not in new_tokens:
                new_tokens["refresh_token"] = refresh_token
            tokens.update(new_tokens)
            _save_tokens(tokens)
            return tokens
        else:
            log.error(f"토큰 갱신 실패: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        log.error(f"토큰 갱신 중 예외: {e}")
        return None


def validate_token():
    """토큰 유효성을 확인하고, 만료되었으면 자동 갱신합니다."""
    tokens = _load_tokens()
    if not tokens:
        log.error("카카오 토큰 파일이 없습니다.")
        return False

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    try:
        response = requests.get(
            "https://kapi.kakao.com/v1/user/access_token_info",
            headers=headers
        )

        if response.status_code == 200:
            log.info(f"카카오 토큰 유효 (남은 시간: {response.json().get('expires_in', 0)}초)")
            return True
        elif response.status_code == 401:
            log.info("액세스 토큰 만료. 갱신 시도...")
            return _refresh_token() is not None
        else:
            log.warning(f"토큰 상태 확인 불가 ({response.status_code}). 갱신 시도...")
            return _refresh_token() is not None
    except Exception as e:
        log.warning(f"토큰 검사 중 오류: {e}")
        return False


# ─────────────────────────────────────────────
# 메시지 전송
# ─────────────────────────────────────────────

def send_message(message, link_url=None):
    """카카오톡 나에게 보내기로 메시지를 전송합니다."""
    if not validate_token():
        log.error("유효한 토큰을 확보하지 못해 메시지를 전송할 수 없습니다.")
        return False

    tokens = _load_tokens()
    if not tokens:
        return False

    cfg = Config.instance()
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    target_url = link_url or cfg.get("github.pages_url", "https://commitkim.github.io")

    # 메시지 본문에 링크 포함
    full_message = f"{message}\n\n🌐 웹 리포트: {target_url}"

    template = {
        "object_type": "text",
        "text": full_message,
        "link": {
            "web_url": target_url,
            "mobile_web_url": target_url
        },
        "button_title": "자세히 보기"
    }

    data = {"template_object": json.dumps(template)}

    try:
        response = requests.post(url, headers=headers, data=data)

        # 토큰 만료 시 자동 갱신 후 재시도
        is_token_error = response.status_code == 401
        if not is_token_error:
            try:
                res_json = response.json()
                if res_json.get('code') == -401:
                    is_token_error = True
            except Exception:
                pass

        if is_token_error:
            log.info("전송 중 토큰 만료. 갱신 후 재시도...")
            new_tokens = _refresh_token()
            if new_tokens:
                headers["Authorization"] = f"Bearer {new_tokens['access_token']}"
                response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200 and response.json().get('result_code') == 0:
            log.info("카카오톡 전송 완료!")
            return True
        else:
            log.error(f"카카오톡 전송 실패: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        log.error(f"메시지 전송 중 예외: {e}")
        return False


# ─────────────────────────────────────────────
# 초기 인증 설정 (Interactive)
# ─────────────────────────────────────────────

def setup_auth():
    """카카오 인증을 설정합니다. (대화형)"""
    cfg = Config.instance()
    api_key = cfg.get_secret("KAKAO_REST_API_KEY")
    client_secret = cfg.get_secret("KAKAO_CLIENT_SECRET")
    redirect_uri = cfg.get("messenger.kakao.redirect_uri", "http://localhost")

    print("\n🔐 카카오 인증 설정")
    print("=" * 50)

    auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={api_key}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code&scope=talk_message"
    )

    print(f"\n1. 아래 URL을 브라우저에서 열어주세요:\n{auth_url}")
    webbrowser.open(auth_url)
    print("\n2. 카카오 로그인 후 '동의하고 계속하기'를 클릭하세요.")
    print("3. 리다이렉트된 URL에서 'code=' 뒤의 값을 복사하세요.")

    auth_code = input("\n인증 코드를 입력하세요: ").strip()

    # 토큰 발급
    data = {
        "grant_type": "authorization_code",
        "client_id": api_key,
        "redirect_uri": redirect_uri,
        "code": auth_code,
        "client_secret": client_secret
    }

    response = requests.post(
        "https://kauth.kakao.com/oauth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
        data=data
    )

    if response.status_code == 200:
        tokens = response.json()
        _save_tokens(tokens)
        print("\n✅ 카카오 인증 완료! 토큰이 저장되었습니다.")
    else:
        print(f"\n❌ 인증 실패: {response.status_code}, {response.text}")
        print("   카카오 개발자 사이트에서 Redirect URI, 동의항목을 확인하세요.")
