# Pixiv API
A pixiv api allows you write your own scripts


## 1. Requirements

python(version >= 3.5)

requests

PIL

aiohttp
   
## 2.Tutorial

#### Create A New Object

Construct a new pixiv object. Ignore username and password if you want use refresh token to login.

```python
pixiv = Pixiv(username=USERNAME, password=PASSWORD)
```

#### Login

```python
pixiv.login()
```

#### Search

Keywords | Type | Default | Notes
--- | --- | --- | ---
word | List of Strings | Must input | 
search_target | Str | 'partial_match_for_tags' | 'partial_match_for_tags', 'exact_match_for_tags', 'title_and_caption'
sort | Str | 'date_desc' | 'date_desc', 'date_asc'
filter | Str | 'for_ios' | 'for_ios'
type | Str | 'illust' | 'illsut', 'novel'

```python
pixiv.search(word=['アイアンマン'])
```

#### Filter

Customize your own query that narrow down search results

Keywords | Type | Default | Notes
--- | --- | --- | ---
views_lower_bound | Int |  |
views_upper_bound | Int |  |
bookmarks_lower_bound | Int |  |
bookmarks_upper_bound | Int |  |
type | Str |  | 'illust', 'manga', 'ugoira'
date_before | Str |  | xxxx-xx-xx(year-month-day)
date_after | Str |  | xxxx-xx-xx(year-month-day)
R_18_filter | Boolean |  |
R_18G_filter | Boolean |  |
rank | Int | | only works with the results you get from ranking method

```python
pixiv.illusts.filter(views_lower_bound=200000, bookmarks_lower_bound=10000)
pixiv.novels.filter(views_lower_bound=5000, bookmarks_lower_bound=2000)
```

#### Download

Download search or filtered results to disk

```python
pixiv.download('path_to_folder')
```

![demo](https://github.com/waka93/PixivDownloader/blob/master/demo/20180702-023013.png)

#### Trending

Get trending tags

Parameters | Type | Default | Notes
--- | --- | --- | ---
type | Str | | 'illust', 'manga', 'novel'

```python
pixiv.trending('illust')  # get trending tags
pixiv.tags.keys()  # view trending tags
```

#### Ranking

Get illust, manga or novel rankings

Parameters | Type | Default | Notes
--- | --- | --- | ---
type | Str | | 'illust', 'manga', 'novel'
mode | Str | | 'daily', 'male', 'female', 'original', 'rookie', 'weekly', 'monthly', 'past'
date | Str | None | xxxx-xx-xx(year-month-day) only works if mode == 'past'

```python
pixiv.ranking('illust', 'daily')  # get daily illust rankings
pixiv.filter(rank=20)  # choose the first 20 illusts
pixiv.download('images')  # download them
```



