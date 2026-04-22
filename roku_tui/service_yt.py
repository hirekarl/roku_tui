from __future__ import annotations

import httpx

class YouTubeClient:
    """Simple client to search YouTube without an API key using the InnerTube API."""

    def __init__(self) -> None:
        self._url = "https://www.youtube.com/youtubei/v1/search"
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    async def search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        """Search YouTube and return a list of video info dicts."""
        payload = {
            "context": {
                "client": {"clientName": "WEB", "clientVersion": "2.20240111.01.00"}
            },
            "query": query,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._url, json=payload, headers=self._headers, timeout=10.0
                )
                resp.raise_for_status()
                data = resp.json()

            results = []
            # Navigate the complex InnerTube response structure
            contents = (
                data.get("contents", {})
                .get("twoColumnSearchResultsRenderer", {})
                .get("primaryContents", {})
                .get("sectionListRenderer", {})
                .get("contents", [])
            )

            for content in contents:
                item_section = content.get("itemSectionRenderer", {}).get(
                    "contents", []
                )
                for item in item_section:
                    video = item.get("videoRenderer")
                    if not video:
                        continue

                    video_id = video.get("videoId")
                    title_runs = video.get("title", {}).get("runs", [{}])
                    title = title_runs[0].get("text", "Unknown")
                    byline_runs = video.get("longBylineText", {}).get("runs", [{}])
                    channel = byline_runs[0].get("text", "Unknown")

                    results.append({"id": video_id, "title": title, "channel": channel})

                    if len(results) >= limit:
                        return results
            return results
        except Exception:
            return []
