from apod import ApodBot
import pytest
from pathlib import Path
from PIL import Image

@pytest.fixture
def testdata():
    def testdata(p: str):
        return (Path(__file__).parent / "testdata" / p).open("rb")
    return testdata

def test_fit_media_scales_image(testdata):
    big_image = testdata("big_image.png")
    out = ApodBot.fit_media(big_image)
    i = Image.open(out.io)
    assert i.width * i.height <= 1080 * 1080

@pytest.mark.xfail  # would fix https://github.com/codl/mastodon-apod/issues/122
def test_fit_media_converts_gif_to_video(testdata):
    animated_gif = testdata("animated.gif")
    out = ApodBot.fit_media(animated_gif)
    assert out.mime.startswith("video/")
