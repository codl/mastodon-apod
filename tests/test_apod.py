from datetime import date

import mastodon
import pytest
import requests

from apod import (
    ApodBot,
    ApodPage,
    ApodScraper,
    ScrapeError,
    cleanup_alt_text,
    guess_date_from_url,
)

test_cases = (
    ApodPage(
        url="https://apod.nasa.gov/apod/ap200609.html",
        # has day gap
        next_url="https://apod.nasa.gov/apod/ap200611.html",
        prev_url="https://apod.nasa.gov/apod/ap200608.html",
        title="Orion over Argentine Mountains",
        credit="Image Credit & Copyright: Nicolas Tabbush",
        # has image and rollover image: clickthru image must be ignored
        media_urls=[
            "https://apod.nasa.gov/apod/image/2006/OrionMountains_Tabbush_960.jpg",
            "https://apod.nasa.gov/apod/image/2006/OrionMountains_Tabbush_960_annotated.jpg",
        ],
        media_mimes=["image/jpeg", "image/jpeg"],
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
    ApodPage(
        # old page format
        url="https://apod.nasa.gov/apod/ap960821.html",
        title="A Close-Up of the Lagoon's Hourglass",
        credit="Credit: J. Trauger (JPL /Caltech), HST, STSci, NASA",
        media_urls=[
            "https://apod.nasa.gov/apod/image/hourglass_hst_big.jpg",
        ],
        media_mimes=[
            "image/jpeg",
        ],
    ),
    ApodPage(
        # older page format
        url="https://apod.nasa.gov/apod/ap950622.html",
        title="The Earth from Apollo 17",
        credit="Picture Credit: NASA, Apollo 17, NSSDC",
        media_urls=[
            "https://apod.nasa.gov/apod/image/earth_a17.gif",
        ],
        media_mimes=[
            "image/gif",
        ],
    ),
    ApodPage(
        # image in button, wildcard <script> tag
        url="https://apod.nasa.gov/apod/ap220424.html",
        title="Split the Universe",
        credit="Image Credit: NASA, Erwin Schrödinger's cat",
        media_urls=[
            "https://apod.nasa.gov/apod/image/1704/SatelliteSale_NASA_960_split3.jpg",
        ],
        media_mimes=[
            "image/jpeg",
        ],
        next_url="https://apod.nasa.gov/apod/ap220425.html",
        prev_url="https://apod.nasa.gov/apod/ap220423.html",
    ),
    ApodPage(
        url="https://apod.nasa.gov/apod/ap211010.html",
        title="Full Moon Silhouettes",
        credit="Video Credit & Copyright: Mark Gee; Music: Tenderness (Dan Phillipson)",
        # has vimeo video
        video_url="https://vimeo.com/58385453",
        prev_url="https://apod.nasa.gov/apod/ap211009.html",
        next_url="https://apod.nasa.gov/apod/ap211011.html",
    ),
    ApodPage(
        url="http://www.star.ucl.ac.uk/~apod/apod/ap231001.html",
        title="A Desert Eclipse",
        credit="Image Credit & Copyright: Maxime Daviron",
        media_urls=[
            "http://www.star.ucl.ac.uk/~apod/apod/image/2310/DesertEclipse_Daviron_2000.jpg",
        ],
        media_mimes=[
            "image/jpeg",
        ],
        prev_url="http://www.star.ucl.ac.uk/~apod/apod/ap230930.html",
        next_url="http://www.star.ucl.ac.uk/~apod/apod/ap231002.html",
        alt="An empty desert is shown with rolling tan sand dunes and a tan glow to the air above. A lone tree grows in the image centre. High above, the Sun glows - but the centre of the Sun is blackened out by an unusual disk.",
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
@pytest.mark.parametrize("page", test_cases, ids=lambda p: p.url.split("/")[-1])
def test_from_html(requests_session: requests.Session, page: ApodPage):
    resp = requests_session.get(page.url)
    resp.raise_for_status()

    assert ApodPage.from_html(page.url, resp.content) == page


@pytest.mark.vcr
def test_link_to_page_doesnt_crash(requests_session: requests.Session):
    URL = "https://apod.nasa.gov/apod/ap241207.html"
    resp = requests_session.get(URL)
    resp.raise_for_status()
    assert ApodPage.from_html(URL, resp.content)


@pytest.mark.parametrize(
    "raw_alt_text, expected",
    [
        (
            # Standard useless alt text
            """See Explanation.  Clicking on the picture will download
the highest resolution version available.""",
            None,
        ),
        (
            # https://apod.nasa.gov/apod/ap220309.html
            """The featured image shows a penny-sized rock on Mars
discovered by the Curiosity Rover in late February 2022.
The rock is unusual because it has several appendages that
make it appear a bit like a flower. 
Please see the explanation for more detailed information.""",
            "The featured image shows a penny-sized rock on Mars discovered by the Curiosity Rover in late February 2022. The rock is unusual because it has several appendages that make it appear a bit like a flower.",
        ),
        (
            # https://apod.nasa.gov/apod/ap210406.html
            "Mars and the Pleiades star cluster set behind one-tree hill. See Explanation.",
            "Mars and the Pleiades star cluster set behind one-tree hill.",
        ),
        pytest.param(
            # https://apod.nasa.gov/apod/ap210414.html
            """A picture of the Pencil Nebula Supernova Shock Wave 
For more details, please read
the explanation.""",
            "A picture of the Pencil Nebula Supernova Shock Wave",
            marks=pytest.mark.skip(
                reason="I'm not sure how to support this "
                "without breaking other more common cases"
            ),
        ),
        (
            # https://apod.nasa.gov/apod/ap220109.html
            """The featured image shows Jupiter full face including the 
Great Red Spot as captured by Hubble in 2016.""",
            "The featured image shows Jupiter full face including the Great Red Spot as captured by Hubble in 2016.",
        ),
        (
            # https://apod.nasa.gov/apod/ap210331.html
            "Polarization of light emitted from the near the black hole M87 is pictured. See Explanation.",
            "Polarization of light emitted from the near the black hole M87 is pictured.",
        ),
        (
            # https://apod.nasa.gov/apod/ap221205.html
            """The featured image shows many blue stars clustered 
together in blue-glowing gas and dust.
Please see the explanation for more detailed information.""",
            "The featured image shows many blue stars clustered together in blue-glowing gas and dust.",
        ),
    ],
)
def test_cleanup_alt_text(raw_alt_text, expected):
    assert cleanup_alt_text(raw_alt_text) == expected


@pytest.fixture
def page_from_url(requests_session):
    def page_from_url(url):
        resp = requests_session.get(url)
        resp.raise_for_status()
        return ApodPage.from_html(url, resp.text)

    return page_from_url


@pytest.mark.vcr
def test_from_html_alt(page_from_url):
    page = page_from_url("https://apod.nasa.gov/apod/ap220420.html")
    assert (
        page.alt
        == "The featured image shows four planets lined up behind the RFK Triboro bridge in New York City. The image was taken just before sunrise two days ago."
    )


@pytest.mark.vcr
@pytest.mark.parametrize(
    ("status_id", "expected"),
    (
        ("109018224046459751", "https://apod.nasa.gov/apod/ap220918.html"),
        ("109069184629858810", "https://apod.nasa.gov/apod/ap220927.html"),
        ("109024311093141985", None),  # a reply
    ),
)
def test_extract_url(status_id, expected):
    m = mastodon.Mastodon(
        api_base_url="https://botsin.space",
        user_agent="mastodon-apod test suite +https://github.com/codl/mastodon-apod",
    )
    status = m.status(status_id)

    assert ApodBot.extract_apod_url_from_status(status) == expected


@pytest.mark.vcr
@pytest.mark.parametrize(
    "url",
    (
        "https://apod.nasa.gov/apod/archivepix.html",
        "https://apod.nasa.gov/apod/lib/aptree.html",
        "https://apod.nasa.gov/apod/calendar/allyears.html",
        "https://apod.nasa.gov/apod/calendar/ca9601.html",
        "https://apod.nasa.gov/apod/calendar/ca2301.html",
        "https://apod.nasa.gov/apod/lib/about_apod.html",
        "https://apod.nasa.gov/apod/ap_faq.html",
        "https://apod.nasa.gov/apod/lib/edlinks.html",
    ),
)
def test_from_html_throws_when_not_image_page(url: str, page_from_url):
    with pytest.raises(ScrapeError):
        page_from_url(url)


@pytest.mark.vcr
def test_scraper_get_last_page():
    scraper = ApodScraper()
    assert scraper.latest_page().url == "https://apod.nasa.gov/apod/ap230211.html"


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://apod.nasa.gov/apod/ap230702.html", date(2023, 7, 2)),
        ("https://apod.nasa.gov/apod/ap950616.html", date(1995, 6, 16)),
        ("https://apod.nasa.gov/apod/index.html", None),
    ),
)
def test_guess_date_from_url(url: str, expected: date | None):
    assert guess_date_from_url(url) == expected


@pytest.mark.vcr
@pytest.mark.xfail
def test_html_video(page_from_url):
    page = page_from_url("https://apod.nasa.gov/apod/ap250324.html")
    assert len(page.media_mimes > 0)
    assert page.media_mimes[0].startswith("video/")
