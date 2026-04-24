from __future__ import annotations

import httpx
import respx

from roku_tui.service_yt import YouTubeClient

_SAMPLE_RESPONSE = {
    "contents": {
        "twoColumnSearchResultsRenderer": {
            "primaryContents": {
                "sectionListRenderer": {
                    "contents": [
                        {
                            "itemSectionRenderer": {
                                "contents": [
                                    {
                                        "videoRenderer": {
                                            "videoId": "dQw4w9WgXcQ",
                                            "title": {
                                                "runs": [
                                                    {"text": "Never Gonna Give You Up"}
                                                ]
                                            },
                                            "longBylineText": {
                                                "runs": [{"text": "Rick Astley"}]
                                            },
                                        }
                                    },
                                    {
                                        "videoRenderer": {
                                            "videoId": "abc123",
                                            "title": {
                                                "runs": [{"text": "Another Video"}]
                                            },
                                            "longBylineText": {
                                                "runs": [{"text": "Some Channel"}]
                                            },
                                        }
                                    },
                                ]
                            }
                        }
                    ]
                }
            }
        }
    }
}


@respx.mock
async def test_search_returns_results() -> None:
    respx.post("https://www.youtube.com/youtubei/v1/search").mock(
        return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
    )
    client = YouTubeClient()
    results = await client.search("rick astley")
    assert len(results) == 2
    assert results[0]["id"] == "dQw4w9WgXcQ"
    assert results[0]["title"] == "Never Gonna Give You Up"
    assert results[0]["channel"] == "Rick Astley"


@respx.mock
async def test_search_respects_limit() -> None:
    respx.post("https://www.youtube.com/youtubei/v1/search").mock(
        return_value=httpx.Response(200, json=_SAMPLE_RESPONSE)
    )
    client = YouTubeClient()
    results = await client.search("rick astley", limit=1)
    assert len(results) == 1


@respx.mock
async def test_search_empty_response() -> None:
    respx.post("https://www.youtube.com/youtubei/v1/search").mock(
        return_value=httpx.Response(200, json={})
    )
    client = YouTubeClient()
    results = await client.search("nothing")
    assert results == []


@respx.mock
async def test_search_http_error_returns_empty() -> None:
    respx.post("https://www.youtube.com/youtubei/v1/search").mock(
        return_value=httpx.Response(500)
    )
    client = YouTubeClient()
    results = await client.search("error case")
    assert results == []


@respx.mock
async def test_search_network_error_returns_empty() -> None:
    respx.post("https://www.youtube.com/youtubei/v1/search").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )
    client = YouTubeClient()
    results = await client.search("network error")
    assert results == []


@respx.mock
async def test_search_skips_non_video_items() -> None:
    response_with_ad = {
        "contents": {
            "twoColumnSearchResultsRenderer": {
                "primaryContents": {
                    "sectionListRenderer": {
                        "contents": [
                            {
                                "itemSectionRenderer": {
                                    "contents": [
                                        {"adRenderer": {"something": "irrelevant"}},
                                        {
                                            "videoRenderer": {
                                                "videoId": "vid1",
                                                "title": {
                                                    "runs": [{"text": "Real Video"}]
                                                },
                                                "longBylineText": {
                                                    "runs": [{"text": "Channel"}]
                                                },
                                            }
                                        },
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }
    }
    respx.post("https://www.youtube.com/youtubei/v1/search").mock(
        return_value=httpx.Response(200, json=response_with_ad)
    )
    client = YouTubeClient()
    results = await client.search("query")
    assert len(results) == 1
    assert results[0]["id"] == "vid1"
