# PixivDownloader
Download images from pixiv in an asynchronous way

This Project allows you download images from famous illustration website [pixiv](https://www.pixiv.net) with your customized query



## 1. Requirements

python(version >= 3.5)

requests

PIL

bs4

aiohttp
   
## 2.Tutorial

#### Query keywords
   
Keywords | Type | Default
--- | ---
tags | List of Strings | Must input
views_low_threshold | Int | None
views_high_threshold | Int | None
likes_low_threshold | Int | None
likes_high_threshold | Int | None
bookmarks_low_threshold | Int | None
bookmarks_high_threshold | Int | None
R_18_filter | Boolean | False
R_18G_filter | Boolean | False

#### Example

Construct a new pixiv object with your customized query

```python
pixiv = Pixiv(
        tags=['スカサハ', 'FGO'],
        bookmarks_low_threshold=10000,
        likes_low_threshold=10000,
        views_low_threshold=200000,
        R_18_filter=True,
        R_18G_filter=True,
    )
```

Set your pixiv ID and password and login in settings.py pixiv with them

```python
pixiv.login()
```

Start searching

```python
pixiv.search()
```

Start downloading

```python
pixiv.download('path_to_folder')
```

Result
```python
Running time: 38.940521001815796
```

![demo](https://github.com/waka93/PixivDownloader/blob/master/images/20180702-023013.png)


