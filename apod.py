import ananas
import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import re
from urllib.parse import urljoin, urlparse
import mimetypes


class ApodBot(ananas.PineappleBot):

    def __init__(self, *args, **kwargs):
        ananas.PineappleBot.__init__(self, *args, **kwargs)
        self.session = requests.Session()
        self.session.headers.update({'user-agent': 'mastodon-apod +https://github.com/codl/mastodon-apod'})

    @ananas.hourly(46)
    def check_apod(self):
        state = self.config.get('state', None)
        if not state:
            ARCHIVE = 'https://apod.nasa.gov/apod/archivepix.html'
            resp = self.session.get(ARCHIVE)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            next_page = urljoin(ARCHIVE, soup.b.a['href'])
        else:
            match = re.match('https://apod.nasa.gov/apod/ap(?P<year>[0-9]{2})(?P<month>[0-9]{2})(?P<day>[0-9]{2}).html', state)
            if not match:
                raise Exception('you fucked up idiot')

            year = int(match.group('year')) + 2000
            month = int(match.group('month'))
            day = int(match.group('day'))

            latest_date = date(year=year, month=month, day=day)
            next_date = latest_date + timedelta(days=1)

            next_page = next_date.strftime('https://apod.nasa.gov/apod/ap%y%m%d.html')

        resp = self.session.get(next_page)
        if resp.status_code == 404:
            return
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        image = soup.img
        iframe = soup.iframe
        if image:
            main = image
            a = image.parent

            image_url = urljoin(next_page, a['href'])
            if urlparse(image_url).hostname != 'apod.nasa.gov':
                image_url = urljoin(next_page, image['src'])
        elif iframe:
            main = iframe
            iframe_url = iframe['src']
            up = urlparse(iframe_url)
            if up.hostname in ('www.youtube.com', 'youtube.com', 'youtu.be'):
                videoid = up.path.split('/')[-1]
                iframe_url = 'https://youtube.com/watch?v={}'.format(videoid)

        for parent in main.parents:
            if parent.name == 'center':
                break
        for sibling in parent.next_siblings:
            if sibling.name == 'center':
                break
        medias = tuple()
        descriptions = list()
        description = str()
        for descendant in sibling.descendants:
            if isinstance(descendant, str):
                description += descendant
            elif descendant.name == 'br':
                descriptions.append(description)
                description = str()
        if description:
            descriptions.append(description)

        descriptions.append("{} #APoD".format(next_page))

        contents = list(map(
            lambda d: re.sub('[\n ]+', ' ', d).strip(),
            descriptions))

        if image:
            mimetype = mimetypes.guess_type(image_url)[0]

            image_resp = self.session.get(image_url)
            image_resp.raise_for_status()

            media = self.mastodon.media_post(image_resp.content, mime_type=mimetype, description=contents[0])
            medias = (media['id'],)
        elif iframe:
            contents.insert(0, iframe_url)

        self.mastodon.status_post('\n\n'.join(contents), media_ids=medias)

        self.config.state = next_page
        self.config.save()
