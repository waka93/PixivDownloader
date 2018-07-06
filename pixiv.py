# Pixiv api

import requests

from PIL import Image
from multiprocessing.dummy import Pool as ThreadPool

import json
import re
import copy
import io

import asyncio
import aiohttp

from pixiv_base import PixivBase


class Pixiv(PixivBase):
    __illust_search_url = 'https://app-api.pixiv.net/v1/search/illust'
    __novel_search_url = 'https://app-api.pixiv.net/v1/search/novel'

    __batch = 30
    __offset_set = set([i*30 for i in range(__batch)])

    illusts = {}

    def personal_data(self):
        if not self.login_data:
            print('Please login first.')
            return None
        else:
            return self.login_data

    def search(self, **kwargs):
        """
        Keywords List:

        search_target: ['partial_match_for_tags', 'exact_match_for_tags', 'title_and_caption']
        filter: ['for_ios']
        sort: ['date_desc', 'date_asc']
        word: List of tags you want to search
        type: ['illsut', 'novel']

        :param kwargs:
        :return:
        """

        assert 'word' in kwargs

        offset = None
        params = {
            'search_target': 'partial_match_for_tags',
            'filter': 'for_ios',
            'sort': 'date_desc',
        }

        if 'type' in kwargs and kwargs['type'] == 'novel':
            base_search_url = self.__novel_search_url
            del kwargs['type']
        else:
            base_search_url = self.__illust_search_url

        if 'offset' in kwargs:
            offset = int(kwargs['offset'])
            assert offset <= 5000
            del kwargs['offset']

        for key, value in kwargs.items():
            params[key] = value

        tags = ''
        for tag in params['word']:
            tags += tag + ' '
        tags = tags.rstrip()
        params['word'] = tags

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._search(base_search_url, params, offset))

        return self

    def filter(self, **kwargs):
        """
        Keywords List:

        views_lower_bound: Int
        views_upper_bound: Int
        bookmarks_lower_bound: Int
        bookmarks_upper_bound: Int
        type: ['illust', 'manga', 'ugoira']
        date_before: str  xxxx-xx-xx
        date_after: str xxxx-xx-xx
        R_18_filter: Boolean
        R_18G_filter: Boolean

        :param kwargs:
        :return:
        """
        if kwargs:

            num_of_thread = 10
            query_info = {}

            for key, value in kwargs.items():
                query_info[key] = value

            if query_info.__contains__('views_lower_bound') and query_info.__contains__('views_upper_bound'):
                assert query_info['views_lower_bound'] <= query_info['views_upper_bound']
            if query_info.__contains__('bookmarks_lower_bound') and query_info.__contains__('bookmarks_upper_bound'):
                assert query_info['bookmarks_lower_bound'] <= query_info['bookmarks_upper_bound']
            if query_info.__contains__('date_before') and query_info.__contains__('date_after'):
                assert query_info['date_before'] >= query_info['date_after']

            illusts_slice = self._dict_slice(self.illusts, num_of_thread)
            params = list(zip(illusts_slice, [query_info for i in range(num_of_thread)]))
            pool = ThreadPool()
            illusts_slice = pool.map(self._filter, params)

            print('{} results found.'.format(len(self._merge_dict(illusts_slice))))
            command = input('Do you want to keep result? Type \'yes\' to keep, \'no\' to abandon.\n-> ')
            while command.upper() not in ['YES', 'NO']:
                command = input('Command not found. Type \'yes\' to keep, \'no\' to abandon.\n-> ')
            if command.upper() == 'YES':
                self.illusts = self._merge_dict(illusts_slice)
            elif command.upper() == 'NO':
                pass

        return self

    def download(self, path):
        if not self.illusts:
            print('No images to download')
            return self

        if not path:
            path = input('Please enter path you want to save demo in\n-> ')
            return self.download(path)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._download(path))

        return self

    def new_from_follows(self):
        pass

    def trending(self, _type):
        if _type.upper() == 'ILLUST':
            return self._trending_illust()
        elif _type.upper() == 'NOVEL':
            return self._trending_novel()

    def recommended(self, _type):
        if _type.upper() == 'ILLUST':
            return self._recommended_illust()
        elif _type.upper() == 'MANGA':
            return self._recommended_manga()
        elif _type.upper() == 'NOVEL':
            return self._recommended_novel()
        elif _type.upper() == 'USER':
            return self._recommended_user()

    def ranking(self, _type):
        if _type.upper() == 'ILLUST':
            return self._illust_ranking()
        elif _type.upper() == 'MANGA':
            return self._manga_ranking()
        elif _type.upper() == 'NOVEL':
            return self._novel_ranking()

    def empty(self):
        self.illusts = {}
        self.__offset_set = set([i*30 for i in range(self.__batch)])
        return self

    async def _search(self, base_search_url, params, offset):
        if offset:
            tasks = []
            for i in range(offset//30 + 1):
                params['offset'] = i*30
                tasks.append(self._get_search_result(base_search_url, params=copy.deepcopy(params)))
            await asyncio.gather(*tasks)
        else:
            while self.__offset_set:
                tasks = []
                for offset in self.__offset_set:
                    params['offset'] = offset
                    tasks.append(self._get_search_result(base_search_url, params=copy.deepcopy(params), offset=offset))
                await asyncio.gather(*tasks)

    async def _get_search_result(self, url, params=None, offset=None):
        proxy = 'http://10.0.0.251:8888'
        if self.access_token and self.token_type:
            self.headers['Authorization'] = self.token_type[0].upper() + self.token_type[1:] + ' ' + self.access_token
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params, proxy=proxy, ssl=False) as response:
                if response.status == 200:
                    response = await response.text()
                    response = json.loads(response)
                    if response['illusts']:
                        for illust in response['illusts']:
                            self.illusts[str(illust['id'])] = illust
                        if offset is not None:
                            if offset + self.__batch * 30 <= 5000:
                                self.__offset_set.add(offset + self.__batch*30)
                            self.__offset_set.remove(offset)
                        await asyncio.sleep(.01)
                    else:
                        if offset:
                            self.__offset_set.remove(offset)
                        await asyncio.sleep(.01)

    @staticmethod
    def _filter(params):
        illusts = params[0]
        query_info = params[1]
        for key, value in copy.copy(illusts).items():
            if query_info.__contains__('views_lower_bound'):
                if not value['total_view'] >= query_info['views_lower_bound']:
                    illusts.pop(key)
                    continue
            if query_info.__contains__('views_upper_bound'):
                if not value['total_view'] <= query_info['views_upper_bound']:
                    illusts.pop(key)
                    continue
            if query_info.__contains__('bookmarks_lower_bound'):
                if not value['total_bookmarks'] >= query_info['bookmarks_lower_bound']:
                    illusts.pop(key)
                    continue
            if query_info.__contains__('bookmarks_upper_bound'):
                if not value['total_bookmarks'] <= query_info['bookmarks_lower_bound']:
                    illusts.pop(key)
                    continue
            if query_info.__contains__('type'):
                if not value['type'] in query_info['type'] or not value['type'] == query_info['type']:
                    illusts.pop(key)
                    continue
            if query_info.__contains__('date_before'):
                if not value['create_date'] <= query_info['date_before']:
                    illusts.pop(key)
                    continue
            if query_info.__contains__('date_after'):
                if not value['create_date'] >= query_info['date_after']:
                    illusts.pop(key)
                    continue
            if query_info.__contains__('R_18_filter'):
                if query_info['R_18_filter'] and 'R-18' in [i['name'] for i in value['tags']]:
                    illusts.pop(key)
                    continue
            if query_info.__contains__('R_18G_filter'):
                if query_info['R_18G_filter'] and 'R-18G' in [i['name'] for i in value['tags']]:
                    illusts.pop(key)
                    continue
        return illusts

    @staticmethod
    def _dict_slice(illusts, num):
        """
        Slice a dict into a list of sub_dict
        :param num: Int
        :param illusts: Dict
        :return: List of dicts
        """
        chunk = len(illusts)//num
        illusts_slice = []
        buffer = {}
        count = 0
        for key, value in illusts.items():
            buffer.update({key:value})
            count += 1
            if count%chunk == 0 and count <= chunk*(num-1):
                illusts_slice.append(buffer)
                buffer = {}
        illusts_slice.append(buffer)
        return illusts_slice

    @staticmethod
    def _merge_dict(illusts_slice):
        """
        Merge dicts into a dict
        :param illusts_slice: List of dicts
        :return: dict
        """
        buffer = {}
        for d in illusts_slice:
            buffer.update(d)
        return buffer

    async def _download(self, path):
        semaphore = asyncio.Semaphore(value=50)

        illust_info = []
        for illust in self.illusts.values():
            if illust['meta_single_page']:
                illust_info.append([illust['title'], illust['user']['name'], illust['meta_single_page']['original_image_url']])
            elif illust['meta_pages']:
                for page in illust['meta_pages']:
                    illust_info.append([illust['title'], illust['user']['name'], page['image_urls']['original']])

        tasks = [self._get_image(semaphore, illust, path) for illust in illust_info]
        await asyncio.gather(*tasks)

    async def _get_image(self, semaphore, illust, path):
        await semaphore.acquire()
        headers = self.headers
        headers['Referer'] = 'https://app-api.pixiv.net/'
        title = illust[0]
        username = illust[1]
        url = illust[2]
        pattern = re.compile(r'.*?p(\d+).(.*?)$')
        _ = re.findall(pattern, url)[0]
        page = _[0]
        suffix = _[1]
        filename = '{title}-{username}-p{page}.{suffix}'.format(
            path=path,
            title=title,
            username=username,
            page=page,
            suffix=suffix,
        )
        print('Downloading', filename)
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    response = await response.read()
                    image = Image.open(io.BytesIO(response))
                    image.save('{path}/{filename}'.format(path=path, filename=filename))
                    image.close()
                else:
                    print('Download Failed', filename)
        semaphore.release()

    def _trending_illust(self):
        pass

    def _trending_novel(self):
        pass

    def _recommended_user(self):
        pass

    def _recommended_illust(self):
        pass

    def _recommended_manga(self):
        pass

    def _recommended_novel(self):
        pass

    def _illust_ranking(self):
        pass

    def _manga_ranking(self):
        pass

    def _novel_ranking(self):
        pass

