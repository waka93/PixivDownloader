# Pixiv api base object

import requests

import json
import copy

import asyncio
import aiohttp

from multiprocessing.dummy import Pool as ThreadPool

from errors import MethodNotImplementedError


class PixivBase:

    __login_url = 'https://oauth.secure.pixiv.net/auth/token'
    __client_secret = 'W9JZoJe00qPvJsiyCGT3CCtC6ZUtdpKpzMbNlUGP'
    __client_id = 'KzEZED7aC0vird8jWyHM38mXjNTY'
    __device_token = 'd9182dabeffd24ebec2582d8d509b8f0'
    __get_secure_url = 'true'
    __include_policy = 'true'

    __grant_type = None
    __refresh_token = None

    access_token = None
    token_type = None

    headers = {
        'App-OS': 'ios',
        'App-OS-Version': '10.3.3',
        'App-Version': '7.1.13',
        'User-Agent': 'PixivIOSApp/7.1.13 (iOS 10.3.3; iPhone7,2)',
    }

    data_form = {
        'client_secret': __client_secret,
        'client_id': __client_id,
        'device_token': __device_token,
        'get_secure_url': __get_secure_url,
        'include_policy': __include_policy,
    }

    def __init__(self, username=None, password=None):
        self.login_data = None
        self.username = username
        self.password = password
        if username and password:
            self.__grant_type = 'password'
        else:
            with open('refresh_token', 'r') as f:
                token = f.read()
                if token:
                    self.__grant_type = 'refresh_token'
                    self.__refresh_token = token

    def login(self):
        """
        login to pixiv
        :return: PixivBase Object
        """
        if self.__grant_type == 'password':
            # Use username and password to login.
            self.data_form['grant_type'] = 'password'
            self.data_form['username'] = self.username
            self.data_form['password'] = self.password
            try:
                resp = requests.post(self.__login_url, headers=self.headers, data=self.data_form, verify=False)
                if resp.status_code == 200:
                    print('Login Success!')
                    self.login_data = json.loads(resp.text)
                    # Login success. Update refresh token, token type and access token.
                    self.__refresh_token = self.login_data['response']['refresh_token']
                    self.token_type = self.login_data['response']['token_type']
                    self.access_token = self.login_data['response']['access_token']
                    with open('refresh_token', 'w') as f:
                        f.write(self.__refresh_token)
                    return self
                else:
                    print('Login Failed! Response Status:', resp.status_code)
                return self
            except Exception as e:
                print(e)
                return self

        elif self.__grant_type == 'refresh_token':
            # Use refresh token to login.
            self.data_form['grant_type'] = 'refresh_token'
            self.data_form['refresh_token'] = self.__refresh_token
            try:
                resp = requests.post(self.__login_url, headers=self.headers, data=self.data_form, verify=False)
                if resp.status_code == 200:
                    print('Login Success!')
                    # Login Success. Update token type and access token.
                    self.login_data = json.loads(resp.text)
                    self.token_type = self.login_data['response']['token_type']
                    self.access_token = self.login_data['response']['access_token']
                    return self
                else:
                    print('Login Failed! Response Status:', resp.status_code)
                    print('Enter your username and password')
                    self.username = input('Enter your username (If you choose to provide refresh token, just press return):\nUsername: ')
                    self.password = input('Enter your password (If you choose to provide refresh token, just press return):\nPassword: ')
                    self.__grant_type = 'password'
                    return self.login()
            except Exception as e:
                print(e)
                return self

        else:
            print('Login Failed! Either provide username and password or refresh token.')
            print('Enter your username and password or paste refresh token to refresh_token')
            self.username = input('Enter your username (If you choose to provide refresh token, just press return):\nUsername: ')
            self.password = input('Enter your password (If you choose to provide refresh token, just press return):\nPassword: ')
            if self.username and self.password:
                self.__grant_type = 'password'
            else:
                self.__grant_type = 'refresh_token'
            return self.login()

    def logout(self, hold=True):
        self.data_form = None
        self.token_type = None
        self.access_token = None
        self.data_form = {
            'client_secret': self.__client_secret,
            'client_id': self.__client_id,
            'device_token': self.__device_token,
            'get_secure_url': self.__get_secure_url,
            'include_policy': self.__include_policy,
        }
        if not hold:
            with open('refresh_token', 'w') as f:
                f.write('')
        return self

    def is_logged_in(self):
        if self.login_data:
            return True
        return False

    async def get_page(self, url, params):
        if self.access_token and self.token_type:
            self.headers['Authorization'] = self.token_type[0].upper() + self.token_type[1:] + ' ' + self.access_token
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    response = await response.text()
                    response = json.loads(response)
                    return response


class PixivDB(dict):
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

        The following parameter only works with the results you get from ranking method
        rank: Int

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

            items_slice = self._dict_slice(self, num_of_thread)
            params = list(zip(items_slice, [query_info for i in range(num_of_thread)]))
            pool = ThreadPool()
            items_slice = pool.map(self._filter, params)

            print('{} results found.'.format(len(self._merge_dict(items_slice))))
            command = input('Do you want to keep result? Type \'yes\' to keep, \'no\' to abandon.\n-> ')
            while command.upper() not in ['YES', 'NO']:
                command = input('Command not found. Type \'yes\' to keep, \'no\' to abandon.\n-> ')
            if command.upper() == 'YES':
                self.empty()
                self.update(self._merge_dict(items_slice))
            elif command.upper() == 'NO':
                pass

        return PixivDB(self)

    def empty(self):
        for key in copy.copy(self).keys():
            self.pop(key)
        return self

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
        items_slice = []
        buffer = {}
        count = 0
        for key, value in illusts.items():
            buffer.update({key:value})
            count += 1
            if count%chunk == 0 and count <= chunk*(num-1):
                items_slice.append(buffer)
                buffer = {}
        items_slice.append(buffer)
        return items_slice

    @staticmethod
    def _merge_dict(items_slice):
        """
        Merge dicts into a dict
        :param items_slice: List of dicts
        :return: dict
        """
        buffer = {}
        for d in items_slice:
            buffer.update(d)
        return buffer




