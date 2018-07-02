# PixivDownloader
Download images from pixiv 

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
views_low_threshold | String
views_high_threshold | String
likes_low_threshold | String
likes_high_threshold | String
bookmarks_low_threshold | String
bookmarks_high_threshold | String
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
   


