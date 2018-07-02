# PixivDownloader
Download images from pixiv in an asynchronous way

This Project allows you download images from famous illustration website [pixiv](https://www.pixiv.net) with your customized query



## 1. Requirements

python(version >= 3.5)

requests

bs4

aiohttp
   
## 2.Tutorial

#### Query keywords
   
Keywords | Type
--- | ---
tags | List of Strings 
views_low_threshold | Int
views_high_threshold | Int
likes_low_threshold | Int
likes_high_threshold | Int
bookmarks_low_threshold | Int
bookmarks_high_threshold | Int
R_18_filter | Boolean
R_18G_filter | Boolean

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

Login pixiv with your pixiv id and password

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


