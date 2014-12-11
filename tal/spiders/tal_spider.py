#!/usr/bin/env python

from __future__ import unicode_literals

from datetime import date
from urlparse import urljoin
from httplib import HTTPConnection

from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request

from tal.items import TALEpisode


THIS_YEAR = date.today().year
FIRST_YEAR = 1995
ARCHIVE_URL = 'http://www.thisamericanlife.org/radio-archives/{0}'
EPISODE_SERVER = 'audio.thisamericanlife.org'
EPISODE_PATH = '/jomamashouse/ismymamashouse/{0}.mp3'
EPISODE_URL = 'http://{EPISODE_SERVER}{EPISODE_PATH}'.format(**locals())


class TALSpider(BaseSpider):
    name = 'tal'
    start_urls = [ARCHIVE_URL.format(year) for year in range(THIS_YEAR, FIRST_YEAR-1, -1)]

    def parse(self, response):
        hxs = HtmlXPathSelector(response)
        episode_urls = hxs.select('//div[@id="archive-episodes"]/div/ul/li/div/h3/a/@href')
        for u in episode_urls:
            this_url = u.extract().encode('utf-8')
            yield Request(urljoin(response.url, this_url), callback=self.parse_episode)

            #episode_num, episode_name = e.extract().strip().split(': ', 1)
            #yield TALEpisode(
            #    id=episode_num.encode('utf-8'),
            #    name=episode_name.encode('utf-8'),
            #    mp3=EPISODE_URL.format(episode_num).encode('utf-8')
            #)

    def parse_episode(self, response):
        hxs = HtmlXPathSelector(response)
        number, title = hxs.select('//h1[contains(concat(" ", normalize-space(@class), " "), " node-title ")]/text()')[0].extract().split(': ', 1)
        pubdate = hxs.select('//div[contains(concat(" ", normalize-space(@class), " "), " node-episode ")]/div[1]/div[1]/div[2]/text()')[0].extract()
        description = hxs.select('//div[contains(concat(" ", normalize-space(@class), " "), " description ")]/text()')[0].extract()

        # Check if mp3 exists
        conn = HTTPConnection(EPISODE_SERVER)
        episode_exists = False
        try:
            conn.request('HEAD', EPISODE_PATH.format(number))
            res = conn.getresponse()
            episode_exists = (res.status == 200)
        except:
            pass

        if episode_exists:
            yield TALEpisode(
                number=number.encode('utf-8'),
                title=title.encode('utf-8'),
                pubdate=pubdate.encode('utf-8'),
                description=description.strip().encode('utf-8'),
                audio_url=EPISODE_URL.format(number).encode('utf-8'),
                link=response.url
            )


