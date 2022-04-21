import requests
from bs4 import BeautifulSoup
from apod import ApodPage
import sys
import csv
from urllib.parse import urljoin
import re

if __name__ == '__main__':
    s = requests.session()
    ARCHIVE = 'https://apod.nasa.gov/apod/archivepix.html'
    resp = s.get(ARCHIVE)
    soup = BeautifulSoup(resp.text, 'html.parser')

    csvw = csv.writer(sys.stdout, dialect="unix")

    for a, _ in zip(soup.find_all("a", href=re.compile("ap[0-9]{6}.html")), range(100)):
        url = urljoin(ARCHIVE, a['href'])

        resp = s.get(url)
        page = ApodPage.from_html(url, resp.text)

        csvw.writerow((page.url, page.alt))
