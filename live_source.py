import re
import pandas as pd
import aiohttp
import asyncio
import functools

from parse_live_source import Parser
from speed_test_async import test_m3u8_speed

file = '直播源.xlsx'
timeout = aiohttp.ClientTimeout(total=10)


def clean(text):
    """
    移除字符串中所有括号及其内容
    """
    text = text.upper()
    cleaned = re.sub(r'\([^)]*\)|\[[^\]]*\]|【[^】]*】', '', text)
    cleaned = re.sub(r'\s+', '', cleaned)
    cleaned = cleaned.replace('HD', '').replace('频道', '')

    return cleaned.strip()


def retry_decorator(max_retries=3):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    print(f"尝试 {attempt + 1}/{max_retries} 失败: {e}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(1)  # 等待一秒后重试
            return None

        return wrapper

    return decorator


def down_live():
    data = pd.read_excel(file, sheet_name='直播源',dtype='str')

    result = []
    for index, row in data.iterrows():
        print(f'正在处理第 {index + 1:2d} 个直播源：{row["直播源地址"]}')
        # print(row['特殊处理'])
        lives = Parser(row['直播源地址'], row['类型'], row['特殊处理']).parse()
        if lives and (lives[1] is not None):
            result.extend(lives)
    print(len(result))

    columns = ['来源','频道组', '频道名称', '频道地址', '频道类型']
    pd_result = pd.DataFrame(result, columns=columns)
    pd_result_drop_duplicates = pd_result.drop_duplicates(subset=['频道地址'], keep='first')
    with pd.ExcelWriter(f'result.xlsx', engine='xlsxwriter',
                        engine_kwargs={'options': {'strings_to_urls': False}}
                        ) as writer:
        pd_result_drop_duplicates.to_excel(writer, index=False)


def process():
    need_data = pd.read_excel(file, sheet_name='需要的频道')
    need_data_dic = {}
    for index, row in need_data.iterrows():
        channel_alias_list = row['频道别名'].split(r'|')
        for channel_alias in channel_alias_list:
            need_data_dic[channel_alias] = {
                "channel_name": row['频道名称'],
                "channel_group_name": row['频道组'],
                "channel_group_id": row['频道组排序'],
                "channel_id": row['频道排序']
            }

    clean_channel_name = []
    clean_channel_group_name = []
    clean_channel_group_id = []
    clean_channel_id = []

    pd_df = pd.read_excel('result.xlsx')
    for index, row in pd_df.iterrows():
        if row['频道名称']:
            clean_name = clean(row['频道名称'])
            if clean_name in need_data_dic:
                clean_channel_name.append(need_data_dic[clean_name]['channel_name'])
                clean_channel_group_name.append(need_data_dic[clean_name]['channel_group_name'])
                clean_channel_group_id.append(need_data_dic[clean_name]['channel_group_id'])
                clean_channel_id.append(need_data_dic[clean_name]['channel_id'])
            else:
                clean_channel_name.append(None)
                clean_channel_group_name.append(None)
                clean_channel_group_id.append(None)
                clean_channel_id.append(None)
        else:
            clean_channel_name.append(None)
            clean_channel_group_name.append(None)
            clean_channel_group_id.append(None)
            clean_channel_id.append(None)

    pd_df['清洗频道名称'] = clean_channel_name
    pd_df['清洗频道组名称'] = clean_channel_group_name
    pd_df['频道组排序'] = clean_channel_group_id
    pd_df['频道排序'] = clean_channel_id

    with pd.ExcelWriter(f'result_clean.xlsx', engine='xlsxwriter',
                        engine_kwargs={'options': {'strings_to_urls': False}}
                        ) as writer:
        pd_df.to_excel(writer, index=False)


@retry_decorator(max_retries=3)
async def async_get_url(url, sem):
    async with sem:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=timeout) as r:
                    status = r.status
                    if status == 200:
                        content = await r.text()
                        if 'feiyang666999/testvideo' in content:  # 剔除测试视频
                            print(f'测试视频：{url}')
                            return 0
                        else:
                            return 1
                    else:
                        return 0
            except Exception as e:
                print(f'直播源地址：{url} 出错，错误信息：{e}')
                return 0


async def verify_is_available():
    data = pd.read_excel('result_clean.xlsx')
    print('总直播源条数：',len(data))
    sem = asyncio.Semaphore(300)  # 协程并发任务量

    availability_tasks = []
    for index, row in data.iterrows():
        # print(f'正在处理 {index} 条')
        url = row['频道地址']
        if pd.notna(row['清洗频道名称']):
            task = async_get_url(url, sem)
            availability_tasks.append(task)
        else:
            availability_tasks.append(asyncio.create_task(asyncio.sleep(0, result=0)))

    availability_results = await asyncio.gather(*availability_tasks, return_exceptions=True)

    connector = aiohttp.TCPConnector(limit=30, ssl=False)  # 可同时并发多个连接
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        speed_tasks = []
        for idx, is_avail in enumerate(availability_results):
            if is_avail == 1:  # 可用
                url = data.iloc[idx]['频道地址']
                task = test_m3u8_speed(url, session, sem)  # 注意：需修改测速函数支持并发
                speed_tasks.append(task)
            else:
                speed_tasks.append(asyncio.create_task(asyncio.sleep(0, result=0)))

        speed_results = await asyncio.gather(*speed_tasks, return_exceptions=True)


    data['地址是否可用'] = availability_results
    data['测试速度'] = [0 if (r is None) or isinstance(r, Exception) else r or 0 for r in speed_results]

    with pd.ExcelWriter(f'result_clean_verify.xlsx', engine='xlsxwriter',
                        engine_kwargs={'options': {'strings_to_urls': False}}
                        ) as writer:
        data.to_excel(writer, index=False)


def generate_live_source():
    data = pd.read_excel('result_clean_verify.xlsx')
    data_filter = data[data['地址是否可用'] == 1]
    data_filter_sort = data_filter.sort_values(
        by=['频道组排序', '频道排序', '测试速度', '频道类型'],
        ascending=[True, True, False, True]
    )
    data_filter_sort_head10 = data_filter_sort.groupby('清洗频道名称').head(10)
    with open('movie_live.m3u', 'w', encoding='utf8') as file:
        file.write('#EXTM3U\n\n')

        channel_group = '央视频道'
        for _, channel in data_filter_sort_head10.iterrows():
            if channel_group != channel["清洗频道组名称"]:
                file.write('\n\n')
                channel_group = channel["清洗频道组名称"]

            file.write(f'#EXTINF:-1 group-title="{channel["清洗频道组名称"]}",{channel["清洗频道名称"]}\n')
            file.write(f'{channel["频道地址"]}\n')

    with open('movie_live.txt', 'w', encoding='utf8') as file:
        channel_group = '央视频道'
        file.write(f'央视频道,#genre#\n')
        for _, channel in data.iterrows():
            if channel_group != channel["清洗频道组名称"]:
                file.write('\n\n')
                channel_group = channel["清洗频道组名称"]
                file.write(f'{channel["清洗频道组名称"]},#genre#\n')

            file.write(f'{channel["清洗频道名称"]},{channel["频道地址"]}\n')


if __name__ == '__main__':
    down_live()
    process()
    asyncio.run(verify_is_available())
    generate_live_source()

