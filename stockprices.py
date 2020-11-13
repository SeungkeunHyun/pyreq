from lxml import html
import requests
import json
from fake_useragent import UserAgent


class StockPrices:
    def __init__(self, app):
        self.app = app
        self.stockCodes = [
            "047820",
            "123690",
            "115180",
            "005930",
            "005935",
            "066570",
            "018260",
            "000660",
            "225190",
            "105560",
            "316140",
        ]
        self.dicStock = list()
        self.uaHeader = {"User-Agent": str(UserAgent().chrome)}

    def getStockInfo(self, uaHeader, dic):
        response = requests.get(dic["url"], headers=uaHeader)
        data = response.content.decode("euc-kr").encode("utf-8")
        dom = html.fromstring(data)
        dic["name"] = dom.xpath("//font[@class='f1']/text()")[0]
        if len(dom.xpath("//font[@class='f3_b']/text()")) > 0:
            dic["price"] = dom.xpath("//font[@class='f3_b']/text()")[0]
            dic["trend"] = "down"
        elif len(dom.xpath("//font[@class='f3_r']/text()")) > 0:
            dic["price"] = dom.xpath("//font[@class='f3_r']/text()")[0]
            dic["trend"] = "up"
        else:
            dic["price"] = dom.xpath("//font[@class='f3']/text()")[0]
            dic["trend"] = "still"
        dic["delta"] = dom.xpath("//span[@id='disArr[0]']/span/text()")[0]
        min_max = dom.xpath("//span[@id='MData[56]']/span/text()")[0]
        dic["max"], dic["min"] = min_max.replace(" ", "").split("/")

    def get(self):
        for scode in self.stockCodes:
            surl = (
                "http://vip.mk.co.kr/newSt/price/price.php?stCode=%s&MSid=&msPortfolioID=" % scode
            )
            dic = {}
            dic["code"] = scode
            dic["url"] = surl
            # dic['header'] = uaHeader
            self.getStockInfo(self.uaHeader, dic)
            self.dicStock.append(dic)
        return self.dicStock
