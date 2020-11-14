from lxml import html, etree
import requests
import json
from fake_useragent import UserAgent
import logging
from logging.handlers import RotatingFileHandler
import datetime
from dateutil.parser import parse
import re
import urllib


class cURLParser(object):
    def __init__(self, req, logger):
        self.uheader = {
            "user-agent": "Mozilla/5.0 (X11; U; UNICOS lcLinux; en-US) Gecko/20140730 (KHTML, like Gecko, Safari/419.3) Arora/0.8.0"
        }
        self.logger = logger
        self.req = req
        self.requri = req.args.get("uri")
        pass

    def run(self):
        pass


class cURLParser_Podbbang(cURLParser):
    def __init__(self, req, logger):
        super().__init__(req, logger)
        self.page_count = 8
        pass

    def fetchEpisodes(self, cid, offset):
        try:
            requri = (
                "https://www.podbbang.com/_m_api/podcasts/%s/episodes?offset=%d&sort=pubdate:desc&limit=%d"
                % (cid, offset, self.page_count)
            )
            self.logger.info("Podbbang uri: %s" % requri)
            response = requests.get(
                "https://phpfetch.herokuapp.com/fetchURL.php?uri=%s" % urllib.parse.quote(requri),
                headers=self.uheader,
            )
            return json.loads(response.content)
        except Exception as err:
            self.logger.error(err)
            return {"data": []}

    def get(self):
        pdoc = {}
        cid = re.match(r".+\/(\d+)$", self.requri).group(1)
        response = requests.get(
            "https://phpfetch.herokuapp.com/fetchURL.php?uri=%s" % urllib.parse.quote(self.requri),
            headers=self.uheader,
        )
        dom = html.fromstring(response.content)
        section = dom.xpath("//div[@class='podcast-details__podcast']")[0]
        pdoc["title"] = section.xpath("//h3[@class='title']/text()")[0]
        pdoc["logo"] = section.xpath("//img[@class='image']/@src")[0]
        pdoc["category"] = section.xpath("//span[@class='category']/a/text()")[0]
        pdoc["author"] = section.xpath("//div[@class='copyright']/text()")[0]
        pdoc["description"] = section.xpath("//div[@class='description']/text()")[0]
        # self.logger.info("response of podbbang main: %s" % response.content)
        offset = 0
        total = 0
        episodes = self.fetchEpisodes(cid, offset)
        # self.logger.info(response.content)
        # dom = html.fromstring(response.content)
        total = episodes["summary"]["total_count"]
        pdoc["episodes"] = []
        while total > len(pdoc["episodes"]):
            self.logger.info("loaded episodes: %d" % len(episodes["data"]))
            for ep in episodes["data"]:
                episode = {}
                episode["title"] = ep["title"]
                episode["pubDate"] = parse(ep["published_at"]).isoformat()
                episode["mediaURI"] = ep["enclosure"]["url"]
                episode["description"] = ep["description"]
                pdoc["episodes"].append(episode)
            offset += len(episodes["data"]) / self.page_count
            self.logger.info("total vs collected: %d vs %d" % (total, len(pdoc["episodes"])))
            episodes = self.fetchEpisodes(cid, offset)
            if len(episodes["data"]) == 0:
                break
        return pdoc


class cURLParser_iTunes(cURLParser):
    def __init__(self, req, logger):
        super().__init__(req, logger)
        self.ns_itunes = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
        self.itunes_map = {
            "title": "/rss/channel/title/text()",
            "logo": "/rss/channel/itunes:image/@href",
            "description": "/rss/channel/description/text()",
            "subtitle": "/rss/channel/itunes:subtitle/text()",
            "author": "/rss/channel/itunes:author/text()",
            "category": "/rss/channel/itunes:category/@text",
            "episodes": {
                "title": "title/text()",
                "subtitle": "itunes:subtitle/text()",
                "summary": "itunes:summary/text()",
                "mediaURI": "enclosure/@url",
                "pubDate": "pubDate/text()",
            },
        }

    def get(self):
        response = requests.get(self.requri)
        dom = etree.XML(response.content)
        pdoc = {}
        for k, v in self.itunes_map.items():
            if "itunes:" in v:
                val = (
                    dom.xpath(v, namespaces=self.ns_itunes)[0]
                    if dom.xpath(v, namespaces=self.ns_itunes)
                    else None
                )
            elif type(v) == dict:
                val = dom.xpath("//item")
                self.logger.info("episode parsing, episodes: %d" % len(val))
                pdoc[k] = []
                for e in val:
                    ep = {}
                    for ik, iv in v.items():
                        # self.logger.info(ik, iv)
                        if "itunes:" in iv:
                            ep[ik] = (
                                e.xpath(iv, namespaces=self.ns_itunes)[0]
                                if e.xpath(iv, namespaces=self.ns_itunes)
                                else None
                            )
                        else:
                            ep[ik] = e.xpath(iv)[0] if e.xpath(iv) else None
                        if ik == "pubDate" and ep[ik]:
                            try:
                                ep[ik] = parse(ep[ik]).isoformat()
                                self.logger.info("pubDate %s" % ep[ik])
                            except Exception as err:
                                self.logger.error(err)
                    pdoc[k].append(ep)
                val = None
            else:
                val = dom.xpath(v)[0] if dom.xpath(v) else None
            if isinstance(val, str):
                pdoc[k] = val
        return pdoc


class cURLParser_Podty(cURLParser_iTunes):
    def __init__(self, req, logger):
        super().__init__(req, logger)
        try:
            cnt = str(requests.get(self.requri).content, encoding="utf-8")
            self.requri = re.search(
                r"window\.clipboardData\.setData\('.+(http[^']+)'\)", cnt
            ).group(1)
            self.logger.info("Podty's rss url: %s" % self.requri)
        except Exception as err:
            self.logger.error(err)

    def get(self):
        return super().get()


class cURL:
    def __init__(self, req, logger):
        self.logger = logger
        self.req = req
        requri = req.args.get("uri")
        if "podbbang" in requri:
            self.parser = cURLParser_Podbbang(req, logger)
        elif "podty" in requri:
            self.parser = cURLParser_Podty(req, logger)
        else:
            self.parser = cURLParser_iTunes(req, logger)

    def get(self):
        return self.parser.get()