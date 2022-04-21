from apod import ApodPage
import requests
import pytest

test_cases = (
    ApodPage(
        url="https://apod.nasa.gov/apod/ap220421.html",
        next_url="https://apod.nasa.gov/apod/ap220422.html",
        prev_url="https://apod.nasa.gov/apod/ap220420.html",
        text="""Apollo 16 Moon Panorama
Image Credit: Apollo 16, NASA; Panorama Assembly: Mike Constantine""",
        title="Apollo 16 Moon Panorama",
        credit="Image Credit: Apollo 16, NASA; Panorama Assembly: Mike Constantine",
        media_url="https://apod.nasa.gov/apod/image/2204/Apollo-16-station-10crop1110.jpg",
        media_mime="image/jpeg",
    ),
    ApodPage(
        url="https://apod.nasa.gov/apod/ap220330.html",
        next_url="https://apod.nasa.gov/apod/ap220331.html",
        prev_url="https://apod.nasa.gov/apod/ap220329.html",
        text="""Animation: Odd Radio Circles
Credits: Illustration: Sam Moorfield; Data: CSIRO, HST (HUDF), ESA, NASA;
Image: J. English (U. Manitoba), EMU, MeerKAT, DES (CTIO); Text: Jayanne English""",
        title="Animation: Odd Radio Circles",
        credit="Credits: Illustration: Sam Moorfield; Data: CSIRO, HST (HUDF), ESA, NASA; Image: J. English (U. Manitoba), EMU, MeerKAT, DES (CTIO); Text: Jayanne English",
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
@pytest.mark.parametrize("page", test_cases)
def test_from_html(requests_session: requests.Session, page: ApodPage):
    resp = requests_session.get(page.url)
    resp.raise_for_status()

    assert ApodPage.from_html(page.url, resp.content) == page
