# Settings for pixiv.py

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36'
}

FORM_DATA = {
    'pixiv_id': '',  # Your login ID
    'captcha': '',
    'g_recaptcha_response': '',
    'password': '',  # Your password
    'post_key': '',
    'source': 'pc',
    'return_to': 'https://www.pixiv.net',
}

NICKNAME = ''  # Your nickname

INDEX_URL = 'http://www.pixiv.net/'
LOGIN_URL = 'https://accounts.pixiv.net/api/login?lang=en'
POSTKEY_URL = 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index'
QUERY_URL = 'https://www.pixiv.net/search.php?word={tags}&order=date_d&p={page}'
ILLUST_URL = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id={illust_id}'

SLEEP_TIME = .5

HOST = 'localhost'
MONGO_DB = ''

IMAGE_NAME = '{user_name}-{illust_title}-p{page}.{suffix}'

