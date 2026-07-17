import pandas as pd
import asyncio
import aiohttp
from pathlib import Path

timeout = aiohttp.ClientTimeout(total=10)

async def async_get_url(url,sem):

    async with sem:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url,timeout=timeout) as r:
                    if r.status == 200:
                        #print(url)
                        return url,1
            except:
                pass

    return url,0


# async def check_count_n(urls,sem,n=3):
#         result=[]
#         for url in urls:
#             counts=n
#             while counts>0:
#                 if async_get_url(url,sem):
#                     result.append((url,True))
#                     break
#                 else:
#                     counts=counts-1


def read_lives_file(file: str):
    with open(file, encoding='utf8') as lives_file:
        lives = lives_file.readlines()

    return lives


def parse_line_group_title(line1):
    line1_splits = line1.split(',')[0].split()
    for line1_split in line1_splits:
        if 'group-title' in line1_split:
            group_title = line1_split.split('=')[1].replace('"', '').replace("'", '')

            return group_title

    return ''


def parse_line_tvg_name(line1):
    line1_splits = line1.split(',')[0].split()
    for line1_split in line1_splits:
        if 'tvg-name' in line1_split:
            tvg_name = line1_split.split('=')[1].replace('"', '').replace("'", '')

            return tvg_name


def parse_line(line1, line2):
    line1 = line1.strip()
    line2 = line2.strip()

    channel_group = channel_name = channel_url = channel_type = tvg_name = ''
    
    if line1.startswith("#EXTINF:") and (line2.startswith("http://[") or line2.startswith("https://[") or line2.startswith("rtp://[")):
        channel_type = 'IPV6'
        channel_name = line1.split(',')[1]
        channel_url = line2
        
        if 'tvg-name' in line1.split(',')[0]:
            tvg_name=parse_line_tvg_name(line1)
        
        channel_group = parse_line_group_title(line1)
        
    elif line1.startswith("#EXTINF:") and (line2.startswith("http") or line2.startswith("rtp://")):
        channel_type = 'IPV4'
        channel_name = line1.split(',')[1]
        channel_url = line2
        
        if 'tvg-name' in line1.split(',')[0]:
            tvg_name=parse_line_tvg_name(line1)
        
        channel_group = parse_line_group_title(line1)

    return channel_group, channel_name, tvg_name, channel_url, channel_type


def parse_file_m3u(file):
    lives_file = read_lives_file(file)
    length = len(lives_file)

    cn = 0
    result = []
    while cn < length - 1:
        channel_group, channel_name, tvg_name, channel_url, channel_type = parse_line(lives_file[cn], lives_file[cn + 1])
        print(lives_file[cn], lives_file[cn + 1])
        print('channel_group:', channel_group)
        print('channel_name:', channel_name)
        print('tvg_name:', tvg_name)
        print('channel_url:', channel_url)
        print('channel_type:', channel_type)
        print('----------------------')
        # if channel_url:
        #     # is_available=requests_live(channel_url)
        #     is_available = 0
        #     cn += 2
        # else:
        #     is_available = ''
        #     cn += 1

        if channel_url:
            #result.append([channel_group, channel_name, channel_url, channel_type, is_available])
            result.append([channel_group, channel_name, tvg_name, channel_url, channel_type])

            cn += 2
        else:
            cn += 1

    return result


def main(file_name):
    result = parse_file_m3u(file_name)
    data = pd.DataFrame(result, columns=['频道组', '频道名称', '频道名称2','频道地址', '频道类型'])

    urls = data['频道地址'].to_list()

    urls_3=urls*3
    sem = asyncio.Semaphore(1000)   #协程并发任务量
    #tasks = [async_get_url(url, sem) for url in urls_3]
    loop = asyncio.get_event_loop()

    tasks=[]
    for url in urls_3:
        task=loop.create_task(async_get_url(url, sem))
        tasks.append(task)

    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

    #解析出收集到的直播源，可用的部分
    tasks_result=[]
    for task in tasks:
        if task.result()[1]==1:
            tasks_result.append(task.result()[0])
    
    tasks_result=list(set(tasks_result))

    
    #与已在使用的直播源进行对比去重
    now_use_data = pd.read_excel('./直播.xlsx', sheet_name='频道源')
    now_use_data_urls=list(set(now_use_data['频道地址'].to_list()))
    
    tasks_result_distinct = list(set(tasks_result).difference(set(now_use_data_urls)))
    
    data_url_result=pd.DataFrame(tasks_result_distinct,columns=['url'],dtype='str')

    data_result=data.merge(data_url_result,left_on='频道地址',right_on='url')

    writer = pd.ExcelWriter(f'./result-{file_name.name}.xlsx', engine='xlsxwriter',
                            engine_kwargs={'options': {'strings_to_urls': False}})
    data_result.to_excel(writer, index=False)
    writer.close()


if __name__=='__main__':
    path = Path('./收集的直播源')
    
    for file in path.iterdir():
        print(file.name)
        main(file)
    
    


