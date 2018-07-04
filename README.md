# Pixiv API
A pixiv api allows you write your own scripts


## 1. Requirements

python(version >= 3.5)

requests

PIL

aiohttp
   
## 2.Tutorial

#### Create A New Object

Construct a new pixiv object. Ignore username and password if you want use refresh token to login

```python
pixiv = Pixiv(username=USERNAME, password=PASSWORD)
```

#### Login

```python
pixiv.login()
```

#### Search

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


