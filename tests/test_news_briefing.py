"""
Unit tests for modules.news_briefing — collector and summarizer

All external network calls (YouTube RSS, YouTubeTranscriptApi, Gemini) are mocked.
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    monkeypatch.setenv("COMMITKIM_ENV", "test")
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    from core.config import Config
    Config._instance = None


# ---------------------------------------------------------------------------
# Tests: collector.find_todays_videos
# ---------------------------------------------------------------------------

class TestFindTodaysVideos:
    RSS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:yt="http://www.youtube.com/xml/schemas/2015">
  <entry>
    <id>yt:video:ABC123</id>
    <yt:videoId>ABC123</yt:videoId>
    <title>{title}</title>
    <link href="https://www.youtube.com/watch?v=ABC123"/>
    <published>2026-02-19T08:00:00+00:00</published>
  </entry>
</feed>"""

    def _make_mock_response(self, title):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = self.RSS_TEMPLATE.format(title=title).encode("utf-8")
        return mock_resp

    def test_finds_matching_video(self):
        """A video with the keyword and today's date in the title should be returned."""
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        title = f"한국경제 {today}🌞#모닝루틴"

        with patch("modules.news_briefing.collector.requests.get") as mock_get:
            mock_get.return_value = self._make_mock_response(title)
            from modules.news_briefing.collector import find_todays_videos
            results = find_todays_videos(channel_id="UCxxx", keyword="모닝루틴")

        assert len(results) == 1
        assert results[0][0] == "ABC123"

    def test_skips_videos_without_keyword(self):
        """Videos not containing the keyword should be skipped."""
        from datetime import datetime
        today = datetime.now().strftime("%Y%m%d")
        title = f"다른 채널 영상 {today}"

        with patch("modules.news_briefing.collector.requests.get") as mock_get:
            mock_get.return_value = self._make_mock_response(title)
            from modules.news_briefing.collector import find_todays_videos
            results = find_todays_videos(channel_id="UCxxx", keyword="모닝루틴")

        assert results == []

    def test_returns_empty_on_http_error(self):
        """Non-200 response should return an empty list without raising."""
        with patch("modules.news_briefing.collector.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 503
            mock_get.return_value = mock_resp

            from modules.news_briefing.collector import find_todays_videos
            results = find_todays_videos(channel_id="UCxxx", keyword="모닝루틴")

        assert results == []

    def test_returns_empty_on_network_exception(self):
        """Network exceptions should be caught and return empty list."""
        with patch("modules.news_briefing.collector.requests.get",
                   side_effect=ConnectionError("no network")):
            from modules.news_briefing.collector import find_todays_videos
            results = find_todays_videos(channel_id="UCxxx", keyword="모닝루틴")

        assert results == []


# ---------------------------------------------------------------------------
# Tests: collector.extract_transcript
# ---------------------------------------------------------------------------

class TestExtractTranscript:
    def test_returns_text_on_success(self):
        """Transcript items should be joined into a single string."""
        mock_item_1 = MagicMock()
        mock_item_1.text = "안녕하세요"
        mock_item_2 = MagicMock()
        mock_item_2.text = "오늘 뉴스입니다"

        mock_transcript = MagicMock()
        mock_transcript.fetch.return_value = [mock_item_1, mock_item_2]

        mock_list = MagicMock()
        mock_list.find_transcript.return_value = mock_transcript

        mock_yt = MagicMock()
        mock_yt.list.return_value = mock_list

        with patch("modules.news_briefing.collector.YouTubeTranscriptApi",
                   return_value=mock_yt):
            from modules.news_briefing import collector
            result = collector.extract_transcript("ABC123")

        assert "안녕하세요" in result
        assert "오늘 뉴스입니다" in result

    def test_returns_none_on_exception(self):
        """Any exception during transcript extraction should return None."""
        with patch("modules.news_briefing.collector.YouTubeTranscriptApi",
                   side_effect=Exception("network error")):
            from modules.news_briefing import collector
            result = collector.extract_transcript("BAD_ID")

        assert result is None


# ---------------------------------------------------------------------------
# Tests: summarizer.summarize
# ---------------------------------------------------------------------------

class TestSummarizer:
    def test_returns_dict_with_expected_keys(self):
        """summarize() should return a dict with kakao_summary and web_report."""
        import json as _json
        expected_output = {
            "main_topics": ["주제1"],
            "key_insights": ["인사이트1"],
            "kakao_summary": "요약입니다",
            "web_report": "## 상세 리포트",
        }

        mock_resp = MagicMock()
        mock_resp.text = _json.dumps(expected_output)

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_resp

        with patch("modules.news_briefing.summarizer.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            # Reset lazy client so our mock is used
            import modules.news_briefing.summarizer as summarizer_mod
            summarizer_mod._client = None
            from core.config import Config
            Config._instance = None
            result = summarizer_mod.summarize("자막 텍스트입니다", "VID123")

        assert result is not None
        assert "kakao_summary" in result
        assert "web_report" in result

    def test_returns_none_on_api_failure(self):
        """If Gemini call fails, summarize() should return None."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("API Error")

        with patch("modules.news_briefing.summarizer.genai") as mock_genai:
            mock_genai.Client.return_value = mock_client
            import modules.news_briefing.summarizer as summarizer_mod
            summarizer_mod._client = None
            from core.config import Config
            Config._instance = None
            result = summarizer_mod.summarize("transcript", "VID999")

        assert result is None
