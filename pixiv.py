import requests
from requests import utils
from bs4 import BeautifulSoup

from PIL import Image

import re
import logging
import json
import time
import io

import aiohttp
import asyncio

from settings import *


class Pixiv:
    logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', level=logging.DEBUG)
    page_to_crawl = set('1')
    crawled_page = set()
    illust_to_crawl = set()
    crawled_illust = set()
    illust_details = {}

    def __init__(self, **kwargs):
        self.index_url = INDEX_URL
        self.login_url = LOGIN_URL
        self.postkey_url = POSTKEY_URL
        self.main_session = requests.Session()
        self.cookies = None
        self.sub_session = requests.Session()
        self.query_info = {
            'tags': None,
            'views_low_threshold': None,
            'views_high_threshold': None,
            'likes_low_threshold': None,
            'likes_high_threshold': None,
            'bookmarks_low_threshold': None,
            'bookmarks_high_threshold': None,
            'time_low_threshold': None,  # not supported yet
            'time_high_threshold': None,  # not supported yet
            'R_18_filter': False,
            'R_18G_filter': False,
            'illust_type': [],  # not supported yet
        }
        if kwargs is not None:
            for key, value in kwargs.items():
                self.query_info[key] = value
        assert type(self.query_info['R_18_filter']) == bool
        assert type(self.query_info['R_18G_filter']) == bool

    def login(self):
        resp = self.main_session.get(self.postkey_url, headers=HEADERS)
        pattern = re.compile(r'post_key".*?"(.*?)"')
        post_key = re.findall(pattern, resp.text)
        form_data = FORM_DATA
        form_data['post_key'] = post_key[0]
        resp = self.main_session.post(self.login_url, headers=HEADERS, data=form_data)
        resp = self.main_session.get(self.index_url, headers=HEADERS)
        cj = self.main_session.cookies
        self.cookies = utils.dict_from_cookiejar(cj)
        pattern = re.compile(r'click-profile"data-click-label="">(.*?)</a>')
        nickname = re.findall(pattern, resp.text)[-1]
        if NICKNAME == nickname:
            logging.info('Login Success!')
        else:
            logging.info('Login Failed')
        return self

    def search(self):
        """
        start searching
        :return: None
        """
        if not self.query_info['tags']:
            print('No query found')
            return self
        logging.info('Start searching...')
        loop = asyncio.get_event_loop()
        logging.info('Retrieving searching results...')
        loop.run_until_complete(self.parse_all_pages())
        logging.info('Filtering illust...')
        loop.run_until_complete(self.parse_all_illust())
        logging.info('Searching finished.')

    def download(self):
        logging.info('Start downloading...')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.download_all_illusts())
        logging.info('downloading finished')

    async def illust_filter_rough(self, illust_table):
        """
        add illustrations that meet query to the crawling list
        :param illust_table: list of dictionaries
        :return: None
        """
        for illust in illust_table:
            if self.is_satisfied_rough(illust):
                self.illust_to_crawl.add(illust['illustId'])
                self.illust_details[illust['illustId']] = illust

    async def parse_one_page(self, page):
        """
        asynchronous parse one searching page
        :param page: str
        :return: None
        """
        async with aiohttp.ClientSession(headers=HEADERS, cookies=self.cookies) as session:
            s = ''
            for tag in self.query_info['tags']:
                s += '%20' + tag
            s = s[3:]
            url = QUERY_URL.format(tags=s, page=page)
            async with session.get(url) as response:
                if response.status == 200:
                    self.crawled_page.add(page)
                    self.page_to_crawl.remove(page)
                    print('Crawling page', page, flush=True)
                    response = await response.text()
                    soup = BeautifulSoup(response, 'lxml')
                    table = soup.select('#js-mount-point-search-result-list')
                    if table:
                        table = json.loads(table[0]['data-items'])
                        await self.illust_filter_rough(table)
                    pages = soup.select('.page-list li a')
                    if pages:
                        for selector in pages:
                            if selector.string not in self.page_to_crawl and selector.string not in self.crawled_page:
                                self.page_to_crawl.add(selector.string)

    async def parse_all_pages(self):
        """
        asynchronous parse all searching pages
        :return: None
        """
        while self.page_to_crawl:
            tasks = [self.parse_one_page(page) for page in self.page_to_crawl]
            await asyncio.gather(*tasks)

    def is_satisfied_rough(self, illust):
        """
        find if an illustration satisfies a query
        :param illust: dict
        :return: boolean
        """
        if self.query_info['bookmarks_low_threshold'] and not illust['bookmarkCount'] >= self.query_info['bookmarks_low_threshold']:
            return False
        if self.query_info['bookmarks_high_threshold'] and not illust['bookmarkCount'] <= self.query_info['bookmarks_high_threshold']:
            return False
        if self.query_info['R_18_filter'] and 'R-18' in illust['tags']:
            return False
        if self.query_info['R_18G_filter'] and 'R-18G' in illust['tags']:
            return False
        return True

    async def illust_filter_meticulous(self, illust_id):
        if not self.is_satisfied_meticulous(illust_id):
            logging.info('{} does not satisfies query'.format(illust_id))
            self.illust_to_crawl.remove(illust_id)
            del self.illust_details[illust_id]
        else:
            logging.info('{} satisfies query'.format(illust_id))

    async def parse_one_illust(self, illust_id):
        """
        asynchronous parse one illustration page
        :param illust_id: str
        :return: None
        """
        url = ILLUST_URL.format(illust_id=illust_id)
        async with aiohttp.ClientSession(headers=HEADERS, cookies=self.cookies) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    response = await response.text()
                    pattern = re.compile(r'urls":{"mini":"(.*?)"')
                    mini_url = re.findall(pattern, response)[0].replace('\\', '')
                    pattern = re.compile(r',"thumb":"(.*?)"')
                    thumb_url = re.findall(pattern, response)[0].replace('\\', '')
                    pattern = re.compile(r',"small":"(.*?)"')
                    small_url = re.findall(pattern, response)[0].replace('\\', '')
                    pattern = re.compile(r',"regular":"(.*?)"')
                    regular_url = re.findall(pattern, response)[0].replace('\\', '')
                    pattern = re.compile(r',"original":"(.*?)"')
                    original_url = re.findall(pattern, response)[0].replace('\\', '')
                    pattern = re.compile(r',"likeCount":(.*?),')
                    likes = re.findall(pattern, response)[0]
                    pattern = re.compile(r',"viewCount":(.*?),')
                    views = re.findall(pattern, response)[0]
                    self.illust_details[illust_id]['mini'] = mini_url
                    self.illust_details[illust_id]['thumb'] = thumb_url
                    self.illust_details[illust_id]['small'] = small_url
                    self.illust_details[illust_id]['regular'] = regular_url
                    self.illust_details[illust_id]['original'] = original_url
                    self.illust_details[illust_id]['likeCount'] = int(likes)
                    self.illust_details[illust_id]['viewCount'] = int(views)
                    await self.illust_filter_meticulous(illust_id)
                else:
                    logging.debug('response code: {}'.format(response.status))

    async def parse_all_illust(self):
        """
        asynchronous parse all illustrations
        :return: None
        """
        tasks = [self.parse_one_illust(illust_id) for illust_id in self.illust_to_crawl]
        await asyncio.gather(*tasks)

    def is_satisfied_meticulous(self, illust_id):
        """
        find if an illustration satisfies a query
        :param illust_id: str
        :return: boolean
        """
        if self.query_info['likes_low_threshold'] and not self.illust_details[illust_id]['likeCount'] >= self.query_info['likes_low_threshold']:
            return False
        if self.query_info['likes_high_threshold'] and not self.illust_details[illust_id]['likeCount'] <= self.query_info['likes_high_threshold']:
            return False
        if self.query_info['views_low_threshold'] and not self.illust_details[illust_id]['viewCount'] >= self.query_info['views_low_threshold']:
            return False
        if self.query_info['views_high_threshold'] and not self.illust_details[illust_id]['viewCount'] <= self.query_info['views_high_threshold']:
            return False
        return True

    async def download_one_page(self, illust_id, page):
        """
        download one page of illustration
        :param illust_id: str
        :param page: str
        :return: None
        """
        logging.info('Downloading illustration {} page {}'.format(illust_id, page))
        headers = HEADERS
        headers['referer'] = ILLUST_URL.format(illust_id=illust_id)
        url = self.illust_details[illust_id]['original']
        pattern = re.compile(r'(.*p)\d+.(.*)$')
        _ = re.findall(pattern, url)[0]
        url = _[0] + page + '.' + _[1]
        suffix = _[1]
        file_name = IMAGE_NAME.format(
            user_name=self.illust_details[illust_id]['userName'],
            illust_title=self.illust_details[illust_id]['illustTitle'],
            page=page,
            suffix=suffix
        )
        async with aiohttp.ClientSession(headers=headers, cookies=self.cookies) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    response = await response.read()
                    image = Image.open(io.BytesIO(response))
                    image.save(file_name)
                    logging.info('Illustration {} page {} saved'.format(illust_id, page))

    async def download_one_illust(self, illust_id):
        """
        asynchronous download given illustration
        :param illust_id: str
        :return: None
        """
        pages = int(self.illust_details[illust_id]['pageCount'])
        tasks = [self.download_one_page(illust_id, str(page)) for page in range(pages)]
        await asyncio.gather(*tasks)
        self.crawled_illust.add(illust_id)
        logging.info('Finished downloading illust {}'.format(illust_id))

    async def download_all_illusts(self):
        """
        asynchronous download all illustrations
        :return: None
        """
        tasks = [self.download_one_illust(illust_id) for illust_id in self.illust_to_crawl]
        await asyncio.gather(*tasks)


if __name__ == '__main__':
    start = time.time()
    pixiv = Pixiv(
        tags=['スカサハ', 'FGO'],
        bookmarks_low_threshold=10000,
        likes_low_threshold=10000,
        views_low_threshold=200000,
        R_18_filter=True,
        R_18G_filter=True,
    )
    pixiv.login()
    pixiv.search()
    pixiv.download()
    print('Running time:', time.time()-start)
