from apod import ApodPage
import requests
import pytest

test_cases = (
    ApodPage(
        url="https://apod.nasa.gov/apod/ap200609.html",
        # has day gap
        next_url="https://apod.nasa.gov/apod/ap200611.html",
        prev_url="https://apod.nasa.gov/apod/ap200608.html",
        title="Orion over Argentine Mountains",
        credit="Image Credit & Copyright: Nicolas Tabbush",
        # has image
        media_url="https://apod.nasa.gov/apod/image/2006/OrionMountains_Tabbush_960.jpg",
        media_mime="image/jpeg",
    ),
    ApodPage(
        url="https://apod.nasa.gov/apod/ap220330.html",
        next_url="https://apod.nasa.gov/apod/ap220331.html",
        prev_url="https://apod.nasa.gov/apod/ap220329.html",
        title="Animation: Odd Radio Circles",
        # several lines of credits                                                      \/ line break is here
        credit="Credits: Illustration: Sam Moorfield; Data: CSIRO, HST (HUDF), ESA, NASA; Image: J. English (U. Manitoba), EMU, MeerKAT, DES (CTIO); Text: Jayanne English",
        # has embedded youtube video
        video_url="https://www.youtube.com/watch?v=m8qvOpcDt1o",
    ),
)


@pytest.fixture
def requests_session():
    session = requests.Session()
    session.headers.update(
        {"user-agent": "mastodon-apod +https://github.com/codl/mastodon-apod"}
    )
    return session


@pytest.mark.vcr
@pytest.mark.parametrize("page", test_cases, ids=lambda p: p.url.split('/')[-1])
def test_from_html(requests_session: requests.Session, page: ApodPage):
    resp = requests_session.get(page.url)
    resp.raise_for_status()

    assert ApodPage.from_html(page.url, resp.content) == page
