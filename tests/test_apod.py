from apod import ApodPage, cleanup_alt_text
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
        media_url="https://apod.nasa.gov/apod/image/2006/OrionMountains_Tabbush_2048.jpg",
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
    ApodPage(
        # old page format
        url="https://apod.nasa.gov/apod/ap960821.html",
        title="A Close-Up of the Lagoon's Hourglass",
        credit="Credit: J. Trauger (JPL /Caltech), HST, STSci, NASA",
        media_url="https://apod.nasa.gov/apod/image/hourglass_hst_big.jpg",
        media_mime="image/jpeg",
    ),
    ApodPage(
        # older page format
        url="https://apod.nasa.gov/apod/ap950622.html",
        title="The Earth from Apollo 17",
        credit="Picture Credit: NASA, Apollo 17, NSSDC",
        media_url="https://apod.nasa.gov/apod/image/earth_a17.gif",
        media_mime="image/gif",
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
        (
            # https://apod.nasa.gov/apod/ap210414.html
            """A picture of the Pencil Nebula Supernova Shock Wave 
For more details, please read
the explanation.""",
            "A picture of the Pencil Nebula Supernova Shock Wave",
        ),
        (
            # https://apod.nasa.gov/apod/ap220109.html
            """The featured image shows Jupiter full face including the 
Great Red Spot as captured by Hubble in 2016."""
            "The featured image shows Jupiter full face including the Great Red Spot as captured by Hubble in 2016."
        ),
        (
            # https://apod.nasa.gov/apod/ap210331.html
            "Polarization of light emitted from the near the black hole M87 is pictured. See Explanation.",
            "Polarization of light emitted from the near the black hole M87 is pictured.",
        ),
    ],
)
def test_cleanup_alt_text(raw_alt_text, expected):
    assert cleanup_alt_text(raw_alt_text) == expected
