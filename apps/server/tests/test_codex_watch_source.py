from app.domains.codex_watch.source import parse_feed, parse_forecast, parse_timeline


def test_timeline_keeps_rejected_preview_as_inference() -> None:
    posts = parse_timeline(
        {
            "events": [
                {
                    "id": "42",
                    "summary": "Enjoy a Codex reset within an hour",
                    "url": "https://x.com/thsottiaux/status/42",
                    "announced_at": "2026-08-13T01:01:37Z",
                    "type": "reset",
                    "source": "live",
                    "confidence": "medium",
                    "reset_verification_status": "rejected",
                    "official_window": {"end_at": "2026-08-13T02:01:37Z"},
                }
            ]
        },
        ["codex", "reset", "quota"],
    )

    assert posts[0].confidence == "inferred"
    assert posts[0].matched_keywords == ["codex", "reset"]
    assert posts[0].official_window_end_at is not None


def test_verified_archive_is_mapped_to_official_confirmation() -> None:
    posts = parse_timeline(
        {
            "events": [
                {
                    "id": "43",
                    "summary": "Usage limits reset for all paid Codex users",
                    "url": "https://x.com/thsottiaux/status/43",
                    "announced_at": "2026-08-11T00:27:44Z",
                    "type": "reset",
                    "source": "archive",
                    "source_label": "Verified archive",
                    "confidence": "high",
                }
            ]
        },
        ["codex", "reset"],
    )

    assert posts[0].confidence == "official"
    assert posts[0].source_label == "Verified archive"


def test_forecast_exposes_only_displayable_model_fields() -> None:
    forecast = parse_forecast(
        {
            "updated_at": "2026-08-19T16:52:41Z",
            "last_reset_at": "2026-08-13T01:01:37Z",
            "probabilities": {"rounded_24h": 30, "rounded_48h": 50},
            "confidence": "medium",
            "time_window": {"label": "11 PM - 2 AM"},
            "cadence": {"recent_median_days": 2.3},
            "model": {"version": "rate-v3"},
        }
    )

    assert forecast.probability_24h == 30
    assert forecast.probability_48h == 50
    assert forecast.model_version == "rate-v3"


def test_localized_feed_merges_translation_with_timeline_evidence() -> None:
    timeline = parse_timeline(
        {
            "events": [
                {
                    "id": "44",
                    "summary": "Usage limits have been reset for all paid users.",
                    "url": "https://x.com/thsottiaux/status/44",
                    "announced_at": "2026-08-20T01:00:00Z",
                    "source": "archive",
                    "confidence": "high",
                }
            ]
        },
        ["reset"],
    )
    feed = parse_feed(
        {
            "locale": "zh",
            "tweets": [
                {
                    "id": "44",
                    "url": "https://x.com/thsottiaux/status/44",
                    "original_text": "Usage limits have been reset for all paid users.",
                    "text": "所有付费用户的用量限制均已重置。",
                    "at": "2026-08-20T01:00:00Z",
                    "is_reply": False,
                    "explicit_reset_claim": True,
                }
            ],
        },
        timeline,
        ["reset"],
    )

    assert feed[0].translated_text == "所有付费用户的用量限制均已重置。"
    assert feed[0].text == "Usage limits have been reset for all paid users."
    assert feed[0].confidence == "official"


def test_forecast_calculates_timeline_statistics() -> None:
    timeline = {
        "updated_at": "2026-08-20T00:00:00Z",
        "events": [
            {
                "type": "reset",
                "source": "archive",
                "confidence": "high",
                "announced_at": "2026-08-10T00:00:00Z",
            },
            {
                "type": "reset",
                "source": "archive",
                "confidence": "high",
                "announced_at": "2026-08-13T00:00:00Z",
            },
            {
                "type": "credits",
                "source": "archive",
                "confidence": "high",
                "announced_at": "2026-08-14T00:00:00Z",
            },
            {
                "type": "reset",
                "source": "archive",
                "confidence": "high",
                "announced_at": "2026-08-19T00:00:00Z",
            },
        ],
    }
    forecast = parse_forecast(
        {
            "updated_at": "2026-08-20T00:00:00Z",
            "probabilities": {"rounded_24h": 30, "rounded_48h": 50},
            "confidence": "medium",
        },
        timeline,
    )

    assert forecast.verified_reset_count == 3
    assert forecast.all_time_median_days == 4.5
    assert forecast.recent_30d_median_days == 4.5
    assert forecast.longest_wait_days == 6.0


def test_confirmed_announcement_is_official_before_it_reaches_the_archive() -> None:
    # Real shape from codex-reset.com: confirmed resets stay out of the archive
    # for a week or more, so they must not wait for it to count as official.
    posts = parse_timeline(
        {
            "events": [
                {
                    "id": "44",
                    "summary": "Day 21/ But today is a reset.",
                    "url": "https://x.com/thsottiaux/status/44",
                    "announced_at": "2026-10-26T06:08:46Z",
                    "type": "reset",
                    "source": "operator-observed",
                    "confidence": "medium",
                    "confirmed": True,
                    "announcement_state": "announced",
                    "observation_result": "reset_observed",
                    "reset_verification_status": "pending",
                },
                {
                    "id": "45",
                    "summary": "Lands tomorrow before 10am PST.",
                    "url": "https://x.com/thsottiaux/status/45",
                    "announced_at": "2026-10-22T06:55:54Z",
                    "type": "reset",
                    "source": "live",
                    "confidence": "medium",
                    "confirmed": False,
                    "announcement_state": "none",
                    "reset_verification_status": "pending",
                },
            ]
        },
        ["reset"],
    )

    assert [post.confidence for post in posts] == ["official", "third_party"]
