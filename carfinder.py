import requests
from bs4 import BeautifulSoup
from hashlib import sha1
from urllib.parse import urlparse
from dataclasses import dataclass

urls = {
    "https://vehiculos.mercadolibre.com.ar/1951-1984/vw-escarabajo#applied_filter_id%3DVEHICLE_YEAR%26applied_filter_name%3DAño%26applied_filter_order%3D7%26applied_value_id%3D1951-1984%26applied_value_name%3D1951-1984%26applied_value_order%3D33%26applied_value_results%3DUNKNOWN_RESULTS%26is_custom%3Dtrue"
}

TELEGRAM_TOKEN = '1855792800:AAF6s08iKuLfBbag_FV8YoRZPeGfhCnYvvA'
TELEGRAM_CHATID = '-593461301'

@dataclass
class Parser:
    website: str
    link_regex: str

    def extract_links(self, contents: str):
        soup = BeautifulSoup(contents, "html.parser")
        ads = soup.select(self.link_regex)
        for ad in ads:
            if 'tracking_id' in ad["href"]:
                href = ad["href"].split('tracking_id')[0]
            else:
                href = ad["href"]

            _id = sha1(href.encode("utf-8")).hexdigest()
            yield {"id": _id, "url": "{}".format(href)}


parsers = [
    Parser(website="https://vehiculos.mercadolibre.com.ar", link_regex="section.ui-search-results ol.ui-search-layout--grid li.ui-search-layout__item div.ui-search-result__wrapper a.ui-search-result__content"),
]

def extract_ads(url, text):
    uri = urlparse(url)
    parser = next(p for p in parsers if uri.hostname in p.website)
    return parser.extract_links(text)


def _main():
    for url in urls:
        res = requests.get(url)
        ads = list(extract_ads(url, res.text))
        seen, unseen = split_seen_and_unseen(ads)

        print("{} seen, {} unseen".format(len(seen), len(unseen)))

        for u in unseen:
            notify(u)

        mark_as_seen(unseen)


def split_seen_and_unseen(ads):
    history = get_history()
    seen = [a for a in ads if a["id"] in history]
    unseen = [a for a in ads if a["id"] not in history]
    return seen, unseen


def get_history():
    try:
        with open("seen.txt", "r") as f:
            return {l.rstrip() for l in f.readlines()}
    except:
        return set()


def notify(ad):
    bot = TELEGRAM_TOKEN
    room = TELEGRAM_CHATID
    url = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}".format(bot, room, ad["url"])
    r = requests.get(url)


def mark_as_seen(unseen):
    with open("seen.txt", "a+") as f:
        ids = ["{}\n".format(u["id"]) for u in unseen]
        f.writelines(ids)


if __name__ == "__main__":
    _main()