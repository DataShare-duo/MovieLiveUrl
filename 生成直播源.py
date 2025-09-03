"""
===========================
@Time : 2024/7/21 1:01
@File : 生成直播源
@Software: PyCharm
@Platform: Win10
@Author : DataShare
===========================
"""
import pandas as pd


data=pd.read_excel('直播.xlsx',sheet_name='频道源',dtype='str',na_filter='')

with open('movie_live.m3u', 'w', encoding='utf8') as file:
    file.write('#EXTM3U\n\n')

    channel_group = '央视频道'
    for _, channel in data.iterrows():
        if channel_group != channel["频道组"]:
            file.write('\n\n')
            channel_group = channel["频道组"]

        file.write(f'#EXTINF:-1 group-title="{channel["频道组"]}",{channel["频道名称"]}\n')

        file.write(f'{channel["频道地址"]}\n')

with open('movie_live.txt', 'w', encoding='utf8') as file:
    channel_group = '央视频道'
    file.write(f'央视频道,#genre#\n')
    for _, channel in data.iterrows():
        if channel_group != channel["频道组"]:
            file.write('\n\n')
            channel_group = channel["频道组"]
            file.write(f'{channel["频道组"]},#genre#\n')

        file.write(f'{channel["频道名称"]},{channel["频道地址"]}\n')

