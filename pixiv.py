# Pixiv api

import requests

from PIL import Image

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

    def personal_info(self):
        if not self.login_data:
            print('Please login first.')
            return None
        else:
            return self.login_data

    def user_detail(self, user_id, filter='for_ios'):
        """
        Get user detail by user id
        :param user_id: Int
        :param filter: Str
        :return:
        """
        base_url = 'https://app-api.pixiv.net/v1/user/detail'
        params = {
            'filter': filter,
            'user_id': user_id,
        }
        response = requests.get(base_url, headers=self.headers, params=params, verify=False)
        if response.status_code == 200:
            return response.text
        return None

    def get_work_by_id(self, _type, _id):
        if self.access_token and self.token_type:
            self.headers['Authorization'] = self.token_type[0].upper() + self.token_type[1:] + ' ' + self.access_token
        if _type.upper() in ['ILLUST', 'MANGA']:
            base_url = 'https://app-api.pixiv.net/v1/illust/detail'
            params = {
                'illust_id': _id
            }
            response = requests.get(base_url, headers=self.headers, params=params, verify=False)
            if response.status_code == 200:
                response = json.loads(response.text)
                self.illusts.append(response['illust'])
        elif _type.upper() == 'NOVEL':
            base_url = 'https://app-api.pixiv.net/v1/novel/detail'
            params = {
                'novel_id': _id
            }
            response = requests.get(base_url, headers=self.headers, params=params, verify=False)
            if response.status_code == 200:
                response = json.loads(response.text)
                self.novels.append(response['novel'])

        return self

    def get_works_by_user_id(self, _type, user_id, filter='for_ios', offset=None):
        """
        Get all works from user. Doesn't require login
        :param _type: Str ['illust', 'manga', 'novel']
        :param user_id: Int
        :param filter: Str
        :param offset: Int
        :return:
        """
        loop = asyncio.get_event_loop()
        if _type.upper() in ['ILLUST', 'MANGA']:
            base_url = 'https://app-api.pixiv.net/v1/user/illusts'
            params = {
                'type': _type.lower(),
                'filter': filter,
                'user_id': user_id,
            }
            loop.run_until_complete(self._search(base_url, params, offset))
        elif _type.upper() == 'NOVEL':
            base_url = 'https://app-api.pixiv.net/v1/user/novel'
            params = {
                'user_id': user_id,
            }
            loop.run_until_complete(self._search(base_url, params, offset))

        return self

    def get_bookmarks_by_user_id(self, _type, user_id, filter='for_ios', restrict='public'):
        """
        Get bookmarks from user
        :param _type: Str ['illust', 'manga', 'novel']
        :param user_id: Int
        :param filter: Str ['for_ios']
        :param restrict: Str ['public']
        :return:
        """

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

    def download(self, path, _type='illust'):
        """
        Download illusts or novels.
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

    def new_from_follows(self, _type='illust', restrict='all'):
        """
        Get new works from followings.
        :param _type: Str ['illust', 'novel']
        :param restrict: Str ['all', 'public', 'private']
        :return:
        """
        loop = asyncio.get_event_loop()
        params = {'restrict': restrict}
        if _type.upper() == 'ILLUST':
            base_url = 'https://app-api.pixiv.net/v2/illust/follow'
            loop.run_until_complete(self._search(base_url, params, offset=660))
        else:
            base_url = 'https://app-api.pixiv.net/v1/novel/follow'
            loop.run_until_complete(self._search(base_url, params, offset=90))

        return self

    def trending(self, _type):
        """
        Get trending tags.
        :param _type: Str ['illust', 'manga', 'novel']
        :return:
        """

        self._trending(_type)

        return self

    def spotlight(self):
        pass

    def recommended(self, _type='illust'):

        loop = asyncio.get_event_loop()

        if _type.upper() == 'ILLUST':
            base_url = 'https://app-api.pixiv.net/v1/illust/recommended'
            params = {
                'include_ranking_illusts': 'true',
                'filter': 'for_ios',
                'include_privacy_policy': 'true',
            }
            loop.run_until_complete(self._search(base_url, params, offset=None))
        elif _type.upper() == 'MANGA':
            loop.run_until_complete(self._recommended_manga())
        elif _type.upper() == 'NOVEL':
            loop.run_until_complete(self._recommended_novel())
        elif _type.upper() == 'USER':
            loop.run_until_complete(self._recommended_user())

        return self

    def ranking(self, _type, mode, date=None):
        """
        Get rankings.
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
        proxy = 'http://10.0.0.251:8888'
        if self.access_token and self.token_type:
            self.headers['Authorization'] = self.token_type[0].upper() + self.token_type[1:] + ' ' + self.access_token
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params, proxy=proxy, ssl=False) as response:
                if response.status == 200:
                    response = await response.text()
                    response = json.loads(response)
                    if response.__contains__('illusts') and response['illusts']:
                        for illust in response['illusts']:
                            self.illusts.append(illust)
                        if offset is not None:
                            if offset + self.__batch * 30 <= 5000:
                                self.__offset_set.add(offset + self.__batch*30)
                            self.__offset_set.remove(offset)
                    elif response.__contains__('novels') and response['novels']:
                        for novel in response['novels']:
                            self.novels.append(novel)
                        if offset is not None:
                            if offset + self.__batch * 30 <= 5000:
                                self.__offset_set.add(offset + self.__batch*30)
                            self.__offset_set.remove(offset)
                    else:
                        if offset:
                            self.__offset_set.remove(offset)

    async def _download_illust(self, path):
        semaphore = asyncio.Semaphore(value=50)

        illust_info = []
        for illust in self.illusts:
            if illust['meta_single_page']:
                illust_info.append([illust['title'], illust['user']['name'], illust['meta_single_page']['original_image_url']])
            elif illust['meta_pages']:
                for page in illust['meta_pages']:
                    illust_info.append([illust['title'], illust['user']['name'], page['image_urls']['original']])

        tasks = [self.__download_illust(semaphore, illust, path) for illust in illust_info]
        await asyncio.gather(*tasks)

    async def __download_illust(self, semaphore, illust, path):
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
        Asynchronous download all novels to path.
        :param path: Str
        :return:
        """
        semaphore = asyncio.Semaphore(value=50)
        novel_info = [[novel['title'], novel['user']['name'], novel['id']] for novel in self.novels]
        tasks = [self.__download_novel(semaphore, novel, path) for novel in novel_info]
        await asyncio.gather(*tasks)

    async def __download_novel(self, semaphore, novel, path):
        """
        Asynchronous download one novel and its series.
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
                        await self.__download_novel(semaphore, novel_prev, path)
                    with open('{path}/{filename}'.format(path=path, filename=filename), 'a+') as f:
                        f.write(response['novel_text'])
                    if response['series_next'] and response['series_next']['id'] not in self.__downloaded_novels:
                        novel_next = [response['series_next']['title'], response['series_next']['user']['name'], response['series_next']['id']]
                        await self.__download_novel(semaphore, novel_next, path)
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
        proxies = {'http': 'http://10.0.0.251:8888'}
        if self.access_token and self.token_type:
            self.headers['Authorization'] = self.token_type[0].upper() + self.token_type[1:] + ' ' + self.access_token
        response = requests.get(url, headers=self.headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            response = json.loads(response.text)
            for item in response['trend_tags']:
                self.tags.append(item['tag'])

    def _recommended_user(self):
        pass

    def _recommended_illust(self):
        base_url = 'https://app-api.pixiv.net/v1/illust/recommended'
        params = {
            'include_ranking_illusts': 'true',
            'filter': 'for_ios',
            'include_privacy_policy': 'true',
        }

    def _recommended_manga(self):
        pass

    def _recommended_novel(self):
        pass

    async def _ranking_illust(self, _type, mode, date):
        """
        Get illust or manga rankings.
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
        proxy = 'http://10.0.0.251:8888'
        if self.access_token and self.token_type:
            self.headers['Authorization'] = self.token_type[0].upper() + self.token_type[1:] + ' ' + self.access_token
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params, proxy=proxy, ssl=False) as response:
                if response.status == 200:
                    response = await response.text()
                    response = json.loads(response)
                    offset = params['offset']
                    if response['illusts']:
                        for rank, illust in enumerate(response['illusts']):
                            illust['rank'] = offset + rank + 1
                            self.illusts.append(illust)

    async def _ranking_novel(self, mode, date):
        """
        Get novel rankings.
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
        proxy = 'http://10.0.0.251:8888'
        if self.access_token and self.token_type:
            self.headers['Authorization'] = self.token_type[0].upper() + self.token_type[1:] + ' ' + self.access_token
        async with aiohttp.ClientSession(headers=self.headers, ) as session:
            async with session.get(url, params=params, proxy=proxy, ssl=False) as response:
                if response.status == 200:
                    response = await response.text()
                    response = json.loads(response)
                    offset = params['offset']
                    if response['novels']:
                        for rank, novel in enumerate(response['novels']):
                            novel['rank'] = offset + rank + 1
                            self.novels.append(novel)
