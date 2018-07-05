# Pixiv api base object

import requests

import json

import asyncio
import aiohttp

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
                    self.username = input('Enter your username (If you choose to provide refresh token, just press return):\n')
                    self.password = input('Enter your password (If you choose to provide refresh token, just press return):\n')
                    return self.login()
            except Exception as e:
                print(e)
                return self

        else:
            print('Login Failed! Either provide username and password or refresh token.')
            print('Enter your username and password or paste refresh token to refresh_token')
            self.username = input('Enter your username (If you choose to provide refresh token, just press return):\n')
            self.password = input('Enter your password (If you choose to provide refresh token, just press return):\n')
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

