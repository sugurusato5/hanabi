import unittest
from unittest.mock import MagicMock, patch

from walkerplus import build_search_url, scrape_walkerplus

SAMPLE_EVENT_HTML = """
<html>
<body>
  <div class="m-mainlist-item">
    <a href="/event/ar0313e605314/">
      <span class="m-mainlist-item__ttl">TOKYO レインボー夏祭り</span>
    </a>
    <a class="m-mainlist-item__img" href="/event/ar0313e605314/">
      <span><img src="//ms-cache.walkerplus.com/walkertouch/wtd/event/14/l/605314.jpg" alt=""></span>
    </a>
  </div>
  <div class="m-mainlist-item">
    <a href="/event/ar0313e603640/">
      <span class="m-mainlist-item__ttl">はてな展</span>
    </a>
    <a class="m-mainlist-item__img" href="/event/ar0313e603640/">
      <span><img src="//ms-cache.walkerplus.com/walkertouch/wtd/event/40/l/603640.jpg" alt=""></span>
    </a>
  </div>
</body>
</html>
"""

EMPTY_EVENT_HTML = "<html><body></body></html>"


def _mock_response(text: str, json_data: dict | None = None) -> MagicMock:
    response = MagicMock()
    response.text = text
    response.json.return_value = json_data or {}
    response.raise_for_status = MagicMock()
    return response


class TestScraper(unittest.TestCase):
    @patch("walkerplus.requests.get")
    def test_scrape_walkerplus_returns_event_list(self, mock_get):
        def side_effect(url, **kwargs):
            if "nominatim.openstreetmap.org" in url:
                return _mock_response(
                    "",
                    {"address": {"ISO3166-2-lvl4": "JP-13"}},
                )
            return _mock_response(SAMPLE_EVENT_HTML)

        mock_get.side_effect = side_effect

        events = scrape_walkerplus(35.6812, 139.7671, "2026-08-17")

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["title"], "TOKYO レインボー夏祭り")
        self.assertEqual(
            events[0]["image_url"],
            "https://ms-cache.walkerplus.com/walkertouch/wtd/event/14/l/605314.jpg",
        )
        self.assertEqual(
            events[0]["link_url"],
            "https://www.walkerplus.com/event/ar0313e605314/",
        )

    @patch("walkerplus.requests.get")
    def test_scrape_walkerplus_returns_empty_list_when_no_events(self, mock_get):
        def side_effect(url, **kwargs):
            if "nominatim.openstreetmap.org" in url:
                return _mock_response(
                    "",
                    {"address": {"ISO3166-2-lvl4": "JP-13"}},
                )
            return _mock_response(EMPTY_EVENT_HTML)

        mock_get.side_effect = side_effect

        events = scrape_walkerplus(35.6812, 139.7671, "2026-08-17")

        self.assertEqual(events, [])

    @patch("walkerplus._latitude_longitude_to_area_code", return_value="ar0313")
    def test_build_search_url(self, _mock_area_code):
        url = build_search_url(35.6812, 139.7671, "2026-08-17")
        self.assertEqual(
            url,
            "https://www.walkerplus.com/event_list/0817/ar0313/",
        )


if __name__ == "__main__":
    unittest.main()
