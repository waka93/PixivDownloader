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

from pixiv_base import PixivBase, PixivDB


class Pixiv(PixivBase):

    __batch = 30
    __offset_set = set([i*30 for i in range(__batch)])

    illusts = PixivDB()  # Store illusts
    novels = PixivDB()  # Store novels
    tags = PixivDB()  # Store trending tags

    __downloaded_novels = set()

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
            base_search_url = 'https://app-api.pixiv.net/v1/search/novel'
            del kwargs['type']
        else:
            base_search_url = 'https://app-api.pixiv.net/v1/search/illust'

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
        This method has been deprecated. Use PixivDB.filter instead
        A filter on illusts. Same as PixivDB.filter
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

        The following parameter only works with the results you get from ranking method
        rank: Int

        :param kwargs:
        :return:
        """

        print('This method has been deprecated. Use PixivDB.filter instead')

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

    def download(self, path, _type='illust'):
        """
        Download illusts or novels
        :param path: Str path to folder
        :param _type: Str ['illust', 'novel']
        :return:
        """
        if _type.upper() == 'ILLUST' and not self.illusts:
            print('No illusts to download')
            return self

        if _type.upper() == 'NOVEL' and not self.novels:
            print('No novels to download')
            return self

        if not path:
            path = input('Please enter path you want to save demo in\n-> ')
            return self.download(path)

        loop = asyncio.get_event_loop()

        if not _type.upper() == 'NOVEL':
            loop.run_until_complete(self._download_illust(path))
        else:
            loop.run_until_complete(self._download_novel(path))

        return self

    def new_from_follows(self):
        pass

    def trending(self, _type):
        """
        Get trending tags
        :param _type: Str ['illust', 'manga', 'novel']
        :return:
        """

        self._trending(_type)

        return self

    def recommended(self, _type):

        loop = asyncio.get_event_loop()

        if _type.upper() == 'ILLUST':
            loop.run_until_complete(self._recommended_illust())
        elif _type.upper() == 'MANGA':
            loop.run_until_complete(self._recommended_manga())
        elif _type.upper() == 'NOVEL':
            loop.run_until_complete(self._recommended_novel())
        elif _type.upper() == 'USER':
            loop.run_until_complete(self._recommended_user())

        return self

    def ranking(self, _type, mode, date=None):
        """
        get rankings
        :param _type: str ['illust', 'manga', 'novel']
        :param mode: str ['daily', 'male', 'female', 'original', 'rookie', 'weekly', 'monthly', 'past']
        :param date: str [xxxx-xx-xx] only works if mode == 'past'
        :return:
        """

        loop = asyncio.get_event_loop()

        if _type.upper() == 'ILLUST' or _type.upper() == 'MANGA':
            loop.run_until_complete(self._ranking_illust(_type, mode, date))
        elif _type.upper() == 'NOVEL':
            loop.run_until_complete(self._ranking_novel(mode, date))

        return self

    def empty(self):
        self.illusts = PixivDB()
        self.novels = PixivDB()
        self.tags = PixivDB()
        self.__offset_set = set([i*30 for i in range(self.__batch)])
        return self


# Below are private methods

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
        if self.access_token and self.token_type:
            self.headers['Authorization'] = self.token_type[0].upper() + self.token_type[1:] + ' ' + self.access_token
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    response = await response.text()
                    response = json.loads(response)
                    if response.__contains__('illusts') and response['illusts']:
                        for illust in response['illusts']:
                            self.illusts[str(illust['id'])] = illust
                        if offset is not None:
                            if offset + self.__batch * 30 <= 5000:
                                self.__offset_set.add(offset + self.__batch*30)
                            self.__offset_set.remove(offset)
                        await asyncio.sleep(.01)
                    elif response.__contains__('novels') and response['novels']:
                        for novel in response['novels']:
                            self.novels[str(novel['id'])] = novel
                        if offset is not None:
                            if offset + self.__batch * 30 <= 5000:
                                self.__offset_set.add(offset + self.__batch*30)
                            self.__offset_set.remove(offset)
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
            if query_info.__contains__('rank'):
                if not value['rank'] <= query_info['rank']:
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

    async def _download_illust(self, path):
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
        title = illust[0].replace('/', ':')
        username = illust[1].replace('/', ':')
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

    async def _download_novel(self, path):
        """
        asynchronous download all novels to path
        :param path: Str
        :return:
        """
        semaphore = asyncio.Semaphore(value=50)
        novel_info = [[novel['title'], novel['user']['name'], novel['id']] for novel in self.novels.values()]
        tasks = [self._get_novel(semaphore, novel, path) for novel in novel_info]
        await asyncio.gather(*tasks)

    async def _get_novel(self, semaphore, novel, path):
        """
        asynchronous download one novel and its series
        :param semaphore: Semaphore object. Control max requests at one time
        :param novel: List
        :param path: Str
        :return:
        """
        await semaphore.acquire()
        if self.access_token and self.token_type:
            self.headers['Authorization'] = self.token_type[0].upper() + self.token_type[1:] + ' ' + self.access_token
        title = novel[0].replace('/', ':')
        username = novel[1].replace('/', ':')
        url = 'https://app-api.pixiv.net/v1/novel/text?novel_id={}'.format(novel[2])
        filename = '{title}-{username}'.format(title=title, username=username)
        self.__downloaded_novels.add(novel[2])
        print('Downloading', filename)
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    response = await response.text()
                    response = json.loads(response)
                    if response['series_prev'] and response['series_prev']['id'] not in self.__downloaded_novels:
                        novel_prev = [response['series_prev']['title'], response['series_prev']['user']['name'], response['series_prev']['id']]
                        await self._get_novel(semaphore, novel_prev, path)
                    with open('{path}/{filename}'.format(path=path, filename=filename), 'a+') as f:
                        f.write(response['novel_text'])
                    if response['series_next'] and response['series_next']['id'] not in self.__downloaded_novels:
                        novel_next = [response['series_next']['title'], response['series_next']['user']['name'], response['series_next']['id']]
                        await self._get_novel(semaphore, novel_next, path)
        semaphore.release()

    def _new_from_follows(self):
        pass

    def _trending(self, _type):
        if _type.upper() == 'ILLUST' or _type.upper() == 'MANGA':
            url = 'https://app-api.pixiv.net/v1/trending-tags/illust?filter=for_ios'
        elif _type.upper() == 'NOVEL':
            url = 'https://app-api.pixiv.net/v1/trending-tags/novel?filter=for_ios'
        else:
            _type = input("Please enter what kind of trending tags you want to get ['illust', 'novel']:\n")
            return self.trending(_type)
        if self.access_token and self.token_type:
            self.headers['Authorization'] = self.token_type[0].upper() + self.token_type[1:] + ' ' + self.access_token
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            response = json.loads(response.text)
            for item in response['trend_tags']:
                self.tags[item['tag']] = item

    def _recommended_user(self):
        pass

    def _recommended_illust(self):
        pass

    def _recommended_manga(self):
        pass

    def _recommended_novel(self):
        pass

    async def _ranking_illust(self, _type, mode, date):
        """
        get illust or manga rankings
        :param mode: str ['daily', 'male', 'female', 'original', 'rookie', 'weekly', 'monthly', 'past']
        :param mode: str [xxxx-xx-xx] only works if mode == 'past'
        :return:
        """

        assert _type.upper() in ['ILLUST', 'MANGA']

        if _type.upper() == 'ILLUST':
            if mode.upper() in ['DAILY', 'MALE', 'FEMALE', 'WEEKLY', 'MONTHLY', 'PAST']:
                offset = 480
            elif mode.upper() in ['ORIGINAL', 'ROOKIE']:
                offset = 270
            else:
                mode = input("Please choose mode in the following list:\n['daily', 'male', 'female', 'original', 'rookie', 'weekly', 'monthly', 'past']\n->")
                if mode.upper() == 'PAST':
                    date = input("Please enter date:\n->")
                return self.ranking('illust', mode, date)

            mode_map = {
                'daily': 'day',
                'male': 'day_male',
                'female': 'day_female',
                'original': 'week_original',
                'rookie': 'week_rookie',
                'weekly': 'week',
                'monthly': 'month',
                'past': 'day',
            }

            params = {
                'mode': mode_map[mode.lower()],
                'filter': 'for_ios',
            }

        else:
            if mode.upper() in ['DAILY', 'PAST']:
                offset = 480
            elif mode.upper() in ['WEEKLY', 'MONTHLY', 'ROOKIE']:
                offset = 90
            else:
                mode = input("Please choose mode in the following list:\n['daily', 'rookie', 'weekly', 'monthly', 'past']\n->")
                if mode.upper() == 'PAST':
                    date = input("Please enter date:\n->")
                return self.ranking('manga', mode, date)

            mode_map = {
                'daily': 'day_manga',
                'rookie': 'week_rookie_manga',
                'weekly': 'week_manga',
                'monthly': 'month_manga',
                'past': 'day_manga',
            }

            params = {
                'mode': mode_map[mode.lower()],
                'filter': 'for_ios',
            }

        if mode.upper() == 'PAST':
            params['date'] = date

        url = 'https://app-api.pixiv.net/v1/illust/ranking'

        tasks = []
        for i in range(offset//30 + 1):
            params['offset'] = i*30
            tasks.append(self._get_ranking_illust(url, params=copy.deepcopy(params)))
        await asyncio.gather(*tasks)

    async def _get_ranking_illust(self, url, params):
        if self.access_token and self.token_type:
            self.headers['Authorization'] = self.token_type[0].upper() + self.token_type[1:] + ' ' + self.access_token
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    response = await response.text()
                    response = json.loads(response)
                    offset = params['offset']
                    if response['illusts']:
                        for rank, illust in enumerate(response['illusts']):
                            self.illusts[str(illust['id'])] = illust
                            self.illusts[str(illust['id'])]['rank'] = offset + rank + 1
                        await asyncio.sleep(.01)

    async def _ranking_novel(self, mode, date):
        """
        get novel rankings
        :param mode: Str ['daily', 'male', 'female', 'rookie', 'weekly', 'past']
        :param date: Str xxxx-xx-xx(year-month-day) only works if mode == 'past'
        :return:
        """

        if mode.upper() in ['DAILY', 'MALE', 'FEMALE', 'ROOKIE', 'WEEKLY', 'PAST']:
            offset = 90
        else:
            mode = input("Please choose mode in the following list:\n['daily', 'male', 'female', 'rookie', 'weekly', 'past']\n->")
            if mode.upper() == 'PAST':
                date = input("Please enter date:\n->")
            return self.ranking('novel', mode, date)

        mode_map = {
            'daily': 'day',
            'male': 'day_male',
            'female': 'day_female',
            'rookie': 'week_rookie',
            'weekly': 'week',
            'past': 'day',
        }

        params = {
            'mode': mode_map[mode.lower()],
            'filter': 'for_ios',
        }

        if mode.upper() == 'PAST':
            params['date'] = date

        url = 'https://app-api.pixiv.net/v1/novel/ranking'

        tasks = []
        for i in range(offset//30 + 1):
            params['offset'] = i*30
            tasks.append(self._get_ranking_novel(url, params=copy.deepcopy(params)))
        await asyncio.gather(*tasks)

    async def _get_ranking_novel(self, url, params):
        if self.access_token and self.token_type:
            self.headers['Authorization'] = self.token_type[0].upper() + self.token_type[1:] + ' ' + self.access_token
        async with aiohttp.ClientSession(headers=self.headers, ) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    response = await response.text()
                    response = json.loads(response)
                    offset = params['offset']
                    if response['novels']:
                        for rank, novel in enumerate(response['novels']):
                            self.novels[str(novel['id'])] = novel
                            self.novels[str(novel['id'])]['rank'] = offset + rank + 1
                        await asyncio.sleep(.01)
