"""
YouTube 영상 수집 및 자막 추출 모듈
- RSS 피드에서 오늘자 영상 검색
- youtube_transcript_api로 한국어 자막 추출

Refactored: uses core.config instead of local config module.
"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import requests
from youtube_transcript_api import YouTubeTranscriptApi

from core.config import Config
from core.logger import get_logger

log = get_logger("news_briefing.collector")


def find_todays_videos(channel_id=None, keyword=None):
    """
    RSS 피드에서 오늘 날짜의 영상을 검색합니다.

    Returns:
        list[tuple]: [(video_id, title, date_str), ...] 형태의 후보 영상 목록
    """
    cfg = Config.instance()
    channel_id = channel_id or cfg.get("news_briefing.youtube_channel_id")
    keyword = keyword or cfg.get("news_briefing.modes.morning.keyword", "모닝루틴")

    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    log.debug(f"RSS 피드 URL: {url}")

    try:
        response = requests.get(url, timeout=15)
        log.debug(f"RSS 응답 코드: {response.status_code}")

        if response.status_code != 200:
            log.error(f"RSS 피드 응답 오류: {response.status_code}")
            return []

        root = ET.fromstring(response.content)
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015'
        }

        entries = root.findall('atom:entry', ns)
        log.debug(f"발견된 영상 수: {len(entries)}")

        today_str = datetime.now().strftime("%Y%m%d")
        log.debug(f"오늘 날짜 기준: {today_str}")

        candidates = []

        for entry in entries:
            title_elem = entry.find('atom:title', ns)
            if title_elem is None:
                continue

            title = title_elem.text
            if keyword not in title:
                continue

            # published 날짜 파싱
            published = entry.find('atom:published', ns).text

            # 제목에서 날짜 추출 (YYYYMMDD)
            date_match = re.search(r'20\d{6}', title)
            if date_match:
                raw_date = date_match.group()
                video_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            else:
                # KST 변환
                try:
                    published_dt = datetime.strptime(published, "%Y-%m-%dT%H:%M:%S+00:00")
                    published_dt = published_dt + timedelta(hours=9)
                    video_date = published_dt.strftime("%Y-%m-%d")
                except Exception:
                    video_date = published[:10]

            video_id = entry.find('yt:videoId', ns).text

            # 오늘 날짜 매칭 확인
            if today_str in title:
                candidates.append((video_id, title, video_date))
                log.info(f"오늘자 영상 발견: {title} ({video_date})")
            else:
                log.debug(f"날짜 불일치 (Skip): {title}")

        return candidates

    except Exception as e:
        log.error(f"RSS 피드 가져오기 실패: {e}")
        return []


def extract_transcript(video_id):
    """
    영상의 한국어 자막을 추출합니다.

    Returns:
        str | None: 전체 자막 텍스트 또는 실패 시 None
    """
    try:
        yt = YouTubeTranscriptApi()

        # list() 메서드로 자막 목록 가져오기
        if hasattr(yt, 'list'):
            transcript_list = yt.list(video_id)
        else:
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            except AttributeError:
                if hasattr(yt, 'get_transcript'):
                    transcript_data = yt.get_transcript(video_id, languages=['ko'])
                    if transcript_data and hasattr(transcript_data[0], 'text'):
                        return " ".join([item.text for item in transcript_data])
                    else:
                        return " ".join([item['text'] for item in transcript_data])
                else:
                    raise Exception("자막 메서드를 찾을 수 없습니다.")

        # 한국어 자막 찾기
        try:
            transcript = transcript_list.find_transcript(['ko'])
        except Exception:
            log.info("한국어 자막 없음, 자동 생성 자막 검색...")
            try:
                transcript = transcript_list.find_generated_transcript(['ko'])
            except Exception:
                log.warning("한국어 자동 생성 자막도 없음.")
                return None

        transcript_data = transcript.fetch()

        if transcript_data:
            first_item = transcript_data[0]
            if hasattr(first_item, 'text'):
                return " ".join([item.text for item in transcript_data])
            else:
                return " ".join([item['text'] for item in transcript_data])

        return None

    except Exception as e:
        log.error(f"자막 추출 오류 ({video_id}): {e}")
        return None
