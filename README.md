# MovieLiveUrl

电影、直播频道播放地址，可以直接利用一些播放器直接观看，而无需下载

`movie_live.m3u`  与  `movie_live.txt `频道地址一样，只是形式不一样，来支持不同的播放器

**每个频道会有多个直播源地址，软件是支持把同一个频道的多直播源进行聚合，显示为一个频道。一个直播源不能用的话，可以切换到另外一个直播源。有的软件支持在多少秒内没有响应，自动切换另外一个直播源**

**名词**：直播源、线路，是同一个意思，不同软件里面显示不一样

# 使用教程
仓库更新迭代时间有点长，里面有各种测试文件比较乱，真实用的文件如下：

- **直播.xlsx**

配置文件，收集的不同直播源，以及抽取需要的频道直播源
- **live_source.py**

主程序，解析不同的直播源，测试是否可用，直播源速度
- **parse_live_source.py**

解析直播的主要逻辑类
- **speed_test_async.py**

测试直播源速度的函数，运用异步的逻辑


**运行程序：**
```txt
python live_source.py
```

**生成直播源结果：**
- movie_live.m3u
- movie_live.txt

生成的文件直播源一模一样，只是2种不同的文件类型，供不同的app使用

**订阅地址：**
- https://raw.githubusercontent.com/DataShare-duo/MovieLiveUrl/refs/heads/main/movie_live.m3u

- https://raw.githubusercontent.com/DataShare-duo/MovieLiveUrl/refs/heads/main/movie_live.txt

# 各端支持的软件

各软件的使用方法，可以在网上查找到相关的使用文档，使用起来其实很简单

## Window端

- PotPlayer

## TV端（基于Android系统）

- TVbox
- DIYP影音

## iOS端

- WhatUp TV
- ntPlayer

## Android端

同TV端

## Mac端

同Window端

# TV端收集的软件

可在 [software](./software) 文件夹 中下载
