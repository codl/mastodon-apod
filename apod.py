import ananas
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta, timezone
import re
from urllib.parse import urljoin, urlparse
import mimetypes
from io import BytesIO
from PIL import Image
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
from dataclasses import dataclass, field
from typing import Optional

urllib3_cn.allowed_gai_family = lambda: socket.AF_INET

class ConfigNotWriteable(Exception):
    pass

class ScrapeError(Exception):
    pass

def cleanup_alt_text(alt:str) -> Optional[str]:
    return alt

@dataclass
class ApodPage():
    url: str
    title: str
    credit: str
    media_url: Optional[str] = None
    media_mime: Optional[str] = None
    video_url: Optional[str] = None
    next_url: Optional[str] = None
    prev_url: Optional[str] = None
    alt: Optional[str] = None

    @classmethod
    def from_html(cls, url:str, html:bytes|str):
        soup = BeautifulSoup(html, 'html.parser')

        image_el = soup.img
        iframe_el = soup.iframe
        media_url = None
        media_mime = None
        video_url = None
        main_el = None
        alt = None

        if image_el and 'src' in image_el.attrs:
            if 'alt' in image_el.attrs:
                alt = image_el['alt']
            for parent in image_el.parents:
                if parent.name == 'a':
                    mime = mimetypes.guess_type(parent['href'])[0]
                    if mime.startswith('image/'):
                        media_mime = mime
                        media_url = urljoin(url, parent['href'])
                        main_el = parent
                    else:
                        raise ScrapeError("Unsupported mimetype {}".format(mime))
                    break

            if not media_url:
                media_url = urljoin(url, image_el['src'])
                media_mime = mimetypes.guess_type(media_url)[0]
                main_el = image_el

        elif iframe_el and 'src' in iframe_el.attrs:
            main_el = iframe_el
            up = urlparse(iframe_el['src'])
            if up.hostname in ('www.youtube.com', 'youtube.com', 'youtu.be'):
                videoid = up.path.split('/')[-1]
                video_url = 'https://www.youtube.com/watch?v={}'.format(videoid)
            else:
                raise ScrapeError("Unsupported iframe {}".format(iframe_el["src"]))
        else:
            raise ScrapeError("Couldn't find main element")

        text_lines:list[str] = []
        line = ""
        for el in main_el.next_elements:
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
                media_url=media_url,
                media_mime=media_mime,
                video_url=video_url,
                title = text_lines[0],
                credit = " ".join(text_lines[1:]),
                next_url = next_url,
                prev_url = prev_url,
                alt = alt,
        )




class ApodBot(ananas.PineappleBot):

    def __init__(self, *args, **kwargs):
        ananas.PineappleBot.__init__(self, *args, **kwargs)
        self.session = requests.Session()
        self.session.headers.update({
            'user-agent':
                'mastodon-apod +https://github.com/codl/mastodon-apod'})


    def start(self):
        self.config['canary'] = datetime.now(tz=timezone.utc)
        succ = self.config.save()
        if not succ:
            self.log("config", "Config could not be written to, this seems bad, shutting down.")
            raise ConfigNotWriteable()
        del self.config['canary']
        self.config.save()

    @ananas.daily(1, 28)
    @ananas.daily(7, 28)
    @ananas.daily(13, 28)
    @ananas.daily(19, 28)
    def check_apod(self):
        next_url = self.config.get('next_url', None)
        if not next_url:

            state = self.config.get('state', None)
            if state:
                # former state tracking mechanism, deprecated 2022-04-21. remove 2023-04-21
                match = re.match('https://apod.nasa.gov/apod/ap(?P<year>[0-9]{2})(?P<month>[0-9]{2})(?P<day>[0-9]{2}).html', state)
                if not match:
                    raise Exception("Couldn't parse 'state' url into a date")

                year = int(match.group('year')) + 2000
                month = int(match.group('month'))
                day = int(match.group('day'))

                latest_date = date(year=year, month=month, day=day)
                next_date = latest_date + timedelta(days=1)

                next_url = next_date.strftime('https://apod.nasa.gov/apod/ap%y%m%d.html')

            else:
                ARCHIVE = 'https://apod.nasa.gov/apod/archivepix.html'
                resp = self.session.get(ARCHIVE)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')
                next_url = urljoin(ARCHIVE, soup.b.a['href'])

        resp = self.session.get(next_url)

        # if it's been more than 24 hours since the last post and we still can't
        # find a new page, check if the url changed
        if resp.status_code == 404 and (
            datetime.now(tz=timezone.utc)
            - self.config.get('last_post_datetime', datetime.min.replace(tzinfo=timezone.utc))
            > timedelta(hours=24)):
            prev_url = self.config.get('prev_url')
            if prev_url:
                prev_resp = self.session.get(prev_url)
                prev_resp.raise_for_status()
                prev_page = ApodPage.from_html(prev_url, prev_resp.text)
                if prev_page.next_url != next_url:
                    next_url = prev_page.next_url
                    resp = self.session.get(next_url)

        if resp.status_code == 404:
            return
        resp.raise_for_status()

        page = ApodPage.from_html(next_url, resp.text)

        post_text = "{page.title}\n\n{page.credits}\n\n{page.url} #APoD".format(page=page)


        medias = None
        if page.media_url:
            if page.media_mime.startswith("image/"):
                image_content = self.fetch_and_fit_image(page.media_url)
                media = self.mastodon.media_post(image_content, mime_type=page.media_mime)
                medias = [media['id'],]
        elif page.video_url:
            post_text = "{}\n\n{}".format(page.video_url, post_text)

        self.mastodon.status_post(post_text, media_ids=medias)

        self.config.next_url = page.next_url
        self.config.prev_url = page.url
        self.config.last_post_datetime = datetime.now(tz=timezone.utc)
        del self.config.state
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

    @ananas.reply
    def force_check(self, _, user):
        if user.acct != self.config.admin:
            return
        self.log("force_check", "Poked by {}, doing a forced check".format(user.acct))
        self.check_apod()
