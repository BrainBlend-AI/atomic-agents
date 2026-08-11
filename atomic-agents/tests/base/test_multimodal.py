from atomic_agents import VideoURL


def test_to_openai_with_url_only():
    content_part = VideoURL(url="https://example.com/clip.mp4").to_openai()

    assert content_part == {"type": "video_url", "video_url": {"url": "https://example.com/clip.mp4"}}


def test_to_openai_with_sampling_parameters():
    content_part = VideoURL(url="https://example.com/clip.mp4", fps=1.0, detail="low").to_openai()

    assert content_part == {
        "type": "video_url",
        "video_url": {"url": "https://example.com/clip.mp4", "fps": 1.0, "detail": "low"},
    }
