import requests
from bs4 import BeautifulSoup
from apod import ApodPage
import sys
import csv
from urllib.parse import urljoin
import re
import time

if __name__ == '__main__':
    s = requests.session()
    s.headers.update({
        'user-agent': 'mastodon-apod +https://github.com/codl/mastodon-apod'})
    ARCHIVE = 'https://apod.nasa.gov/apod/archivepix.html'
    resp = s.get(ARCHIVE)
    soup = BeautifulSoup(resp.text, 'html.parser')

    with open('alts.csv', 'w') as altsf:
        with open('alts_abnormal.csv', 'w') as altsabf:
            csvw = csv.writer(altsf, dialect="unix")
            ab_csvw = csv.writer(altsabf, dialect="unix")

            delay = .1

            for a in soup.find_all("a", href=re.compile("ap[0-9]{6}.html")):
                url = urljoin(ARCHIVE, a['href'])
                print(url)

                resp = None
                while not resp or resp.status_code != 200:
                    time.sleep(delay)
                    resp = s.get(url)
                    if resp.status_code != 200:
                        resp = None
                        delay *= 2
                        print("Raising delay to {}".format(url, delay))
                page = ApodPage.from_html(url, resp.text)

                csvw.writerow((page.url, page.alt))

                if page.alt and not page.alt.startswith("See Explanation.") and not page.alt.endswith("Please see the explanation for more detailed information."):
                    ab_csvw.writerow((page.url, page.alt))

