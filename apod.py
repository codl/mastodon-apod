from functools import cached_property
import ananas
import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta, timezone
import re
from urllib.parse import urljoin, urlparse
import mimetypes
from io import BytesIO
from PIL import Image
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
from dataclasses import dataclass, field
from typing import Optional, Any
from itertools import chain, count
from mastodon import Mastodon
import dataclasses

urllib3_cn.allowed_gai_family = lambda: socket.AF_INET

APOD_URL_RE = re.compile(r'https://apod.nasa.gov/apod/ap(?P<year>[0-9]{2})(?P<month>[0-9]{2})(?P<day>[0-9]{2}).html')

class ConfigNotWriteable(Exception):
    pass

class ScrapeError(Exception):
    pass

def cleanup_alt_text(alt:str) -> Optional[str]:
    sentences = list()
    for sentence in re.split(r"\.\s+", alt):
        sentence = re.sub(r"[\n ]+", " ", sentence)
        if re.search(r"[Ss]ee ([Tt]he )?[Ee]xplanation", sentence):
            break
        if sentence:
            sentences.append(sentence)

    alt = ". ".join(sentences)
    if not alt:
        return None

    if alt[-1] not in "?!.":
        alt += "."

    return alt


def guess_date_from_url(url:str) -> Optional[date]:
    match = re.match(APOD_URL_RE, url)
    if not match:
        return None
    year = int(match['year'])
    month = int(match['month'])
    day = int(match['day'])
    return date(year, month, day)



@dataclass
class ApodPage():
    url: str
    title: str
    credit: str
    media_urls: list[str] = field(default_factory=list)
    media_mimes: list[str] = field(default_factory=list)
    video_url: Optional[str] = None
    next_url: Optional[str] = None
    prev_url: Optional[str] = None
    alt: Optional[str] = None

    @classmethod
    def from_html(cls, url:str, html:bytes|str):
        soup = BeautifulSoup(html, 'html.parser')

        image_el = soup.img
        iframe_el = soup.iframe
        media_urls= []
        media_mimes = []
        video_url = None
        main_el = None
        alt = None

        if image_el and 'src' in image_el.attrs:
            if 'alt' in image_el.attrs:
                alt = image_el['alt']

            # look for rollover image
            found_rollover = False
            for el in chain([image_el], image_el.parents):
                if 'onmouseover' in el.attrs:
                    match = re.search(
                        r"document\.[^.]+\.src\w*=\w*'([^']+)'",
                        el['onmouseover'])
                    if match:
                        found_rollover = True
                        media_urls.append(urljoin(url, match.group(1)))
                        media_mimes.append(mimetypes.guess_type(media_urls[-1])[0])
                        break

            if not found_rollover: # if there is a rollover image, we ignore the link
                for parent in image_el.parents:
                    if parent.name == 'a':
                        mime = mimetypes.guess_type(parent['href'])[0]
                        if mime.startswith('image/'):
                            media_mimes = [mime]
                            media_urls = [urljoin(url, parent['href'])]
                            main_el = parent
                        else:
                            raise ScrapeError("Unsupported mimetype {}".format(mime))
                        break

            if found_rollover or not media_urls:
                media_urls.insert(0, urljoin(url, image_el['src']))
                media_mimes.insert(0, mimetypes.guess_type(media_urls[0])[0])
                main_el = image_el


        elif iframe_el and 'src' in iframe_el.attrs:
            main_el = iframe_el
            up = urlparse(iframe_el['src'])
            if up.hostname in ('www.youtube.com', 'youtube.com', 'youtu.be'):
                videoid = up.path.split('/')[-1]
                video_url = 'https://www.youtube.com/watch?v={}'.format(videoid)
            elif up.hostname in ('player.vimeo.com'):
                videoid = up.path.split('/')[-1]
                video_url = 'https://vimeo.com/{}'.format(videoid)
            else:
                raise ScrapeError("Unsupported iframe {}".format(iframe_el["src"]))
        else:
            raise ScrapeError("Couldn't find main element")

        text_lines:list[str] = []
        line = ""
        els = main_el.next_elements
        restart = True
        while restart:
            restart = False
            for el in els:
                if el.name == 'script':
                    # skip it and its contents by starting the search from there
                    els = chain([el.next_sibling], el.next_sibling.next_elements)
                    restart = True
                    break
                if isinstance(el, str):
                    line += el
                    if line.strip().startswith("Explanation:"):
                        break
                elif not el or el.name in ("br", "p"):
                    if line.strip() != "":
                        text_lines.append(line)
                    line = ""

        text_lines = [re.sub('[\n ]+', ' ', l).strip() for l in text_lines]

        prev_el = soup.find("a", string="<")
        next_el = soup.find("a", string=">")
        prev_url = urljoin(url, prev_el['href']) if prev_el else None
        next_url = urljoin(url, next_el['href']) if next_el else None


        return cls(
                url=url,
                media_urls=media_urls,
                media_mimes=media_mimes,
                video_url=video_url,
                title = text_lines[0],
                credit = " ".join(text_lines[1:]),
                next_url = next_url,
                prev_url = prev_url,
                alt = cleanup_alt_text(alt) if alt else None,
        )



class ApodScraper(object):
    def __init__(self, session:None|requests.Session=None):
        self.session: requests.Session
        if session is not None:
            self.session = session;
        else:
            self.session = requests.Session()
            self.session.headers.update({
                'user-agent':
                    'mastodon-apod +https://github.com/codl/mastodon-apod'})

    def latest_page(self) -> ApodPage:
        IDX_URL = "https://apod.nasa.gov/apod/"
        r = self.session.get(IDX_URL)
        r.raise_for_status()
        page = ApodPage.from_html(IDX_URL, r.content);
        if page.prev_url is None:
            raise ScrapeError("Index page has no previous link")
        prev_r = self.session.get(page.prev_url);
        prev_r.raise_for_status()
        prev_page = ApodPage.from_html(page.prev_url, prev_r.content);
        if prev_page.next_url is None:
            raise ScrapeError("Previous page has no next link")
        page = dataclasses.replace(page, url=prev_page.next_url)
        return page


class ApodBot(ananas.PineappleBot):
    mastodon: Mastodon

    def __init__(self, *args, **kwargs):
        ananas.PineappleBot.__init__(self, *args, **kwargs)
        self.session = requests.Session()
        self.session.headers.update({
            'user-agent':
                'mastodon-apod +https://github.com/codl/mastodon-apod'})
        self.scraper = ApodScraper(session = self.session)

    @ananas.daily(1, 28)
    @ananas.daily(7, 28)
    @ananas.daily(13, 28)
    @ananas.daily(19, 28)
    def check_apod(self):

        recent_urls = self.get_recent_urls()
        if recent_urls:
            last_url = recent_urls[0]
            resp = self.session.get(last_url)
            resp.raise_for_status()
            last_page = ApodPage.from_html(last_url, resp.content)
            if not last_page.next_url:
                raise Exception("Last page doesn't have a next page")
            next_url = last_page.next_url
            resp = self.session.get(next_url)

            if resp.status_code == 404:
                return
            resp.raise_for_status()
            page = ApodPage.from_html(next_url, resp.text)

            if next_url in recent_urls:
                raise Exception("Next page has been posted recently")

            next_date = guess_date_from_url(next_url)
            last_date = guess_date_from_url(last_url)
            if next_date and last_date and next_date <= last_date:
                raise Exception("Date guessed from next page url seems to be in the past")

        else:
            page = self.scraper.latest_page()


        post_text = "{page.title}\n\n{page.credit}\n\n{page.url} #APOD".format(page=page)

        medias = []
        for media_url, mime, i in zip(page.media_urls, page.media_mimes, count()):
            if mime.startswith("image/"):
                image_content = self.fetch_and_fit_image(media_url)
                if i == 0:
                    alt = page.alt
                else:
                    alt = None
                media = self.mastodon.media_post(
                        image_content,
                        mime_type=mime,
                        description=alt)
                medias.append(media['id'])
        if page.video_url:
            post_text = "{}\n\n{}".format(page.video_url, post_text)

        self.mastodon.status_post(post_text, media_ids=medias)

        for key in ("state", "prev_url", "next_url", "last_post_datetime", "canary"):
            changed = False
            if key in self.config:
                # change to a del once <https://github.com/chr-1x/ananas/issues/27> is fixed
                self.config[key] = None
                changed = True
            if changed:
                self.config.save()

    def fetch_and_fit_image(self, image_url):
        """returns a BytesIO"""
        image_resp = self.session.get(image_url)
        image_resp.raise_for_status()

        imageio = BytesIO(image_resp.content)
        outio = BytesIO()

        image = Image.open(imageio)
        image.thumbnail((1080, 1080))
        image.save(outio, image.format)
        outio.seek(0)
        return outio

    @cached_property
    def my_uid(self):
        return self.mastodon.account_verify_credentials()['id']

    def get_recent_urls(self) -> list[str]:
        statuses = self.mastodon.account_statuses(self.my_uid, exclude_replies=True, limit=40)
        urls: list[str] = list()
        for status in statuses:
            url = self.extract_apod_url_from_status(status)
            if url:
                urls.append(url)
        return urls


    @classmethod
    def extract_apod_url_from_status(cls, post: dict[str, Any]) -> str | None:
        eligible = False
        for tag in post["tags"]:
            name:str = tag['name']
            if name.lower() == 'apod':
                eligible = True
        if not eligible:
            return None
        else:
            soup = BeautifulSoup(post["content"], 'html.parser')
            url = None
            for a in soup.find_all("a"):
                if re.match(APOD_URL_RE, a['href']):
                    url = a['href']
            return url



    @ananas.reply
    def force_check(self, _, user):
        if user.acct != self.config.admin:
            return
        self.log("force_check", "Poked by {}, doing a forced check".format(user.acct))
        self.check_apod()
