import pandas as pd
import asyncio
import aiohttp

timeout = aiohttp.ClientTimeout(total=10)

async def async_get_url(url,sem,session):

    async with sem:
        try:
            async with session.get(url,timeout=timeout) as r:
                if r.status == 200:
                    #print(url)
                    return url,1
        except aiohttp.ClientError as e:
            print(f"请求错误：{url},错误：{e}")
        except Exception as e:
            print(f"其他错误: {url}, 错误: {e}")

    return url,0


async def main_urls(urls):
    urls_3 = urls * 3
    sem = asyncio.Semaphore(300)  # 协程并发任务量
    # tasks = [async_get_url(url, sem) for url in urls_3]
    # loop = asyncio.get_event_loop()

    # 创建 aiohttp 的 ClientSession，避免每次请求都重新创建
    async with aiohttp.ClientSession() as session:
        tasks = [async_get_url(url, sem, session) for url in urls_3]
        results = await asyncio.gather(*tasks)

    # tasks = []
    # for url in urls_3:
    #     task = async_get_url(url, sem)
    #     tasks.append(task)
    #
    # # loop.run_until_complete(asyncio.wait(tasks))
    # # loop.close()
    # results = await asyncio.gather(*tasks)

    return results


def main():
    data = pd.read_excel('直播.xlsx', sheet_name='历史积累')
    urls = data['频道地址'].to_list()
    tasks = asyncio.run(main_urls(urls))

    # 解析出收集到的直播源，可用的部分
    tasks_result = []
    for task in tasks:
        # print(task)
        if task[1] == 1:
            tasks_result.append(task[0])

    tasks_result = list(set(tasks_result))
    print("可用的地址数量为：",len(tasks_result))
    print("开始生成结果")
    data_result=pd.DataFrame(tasks_result,columns=['url'])

    with pd.ExcelWriter(f'./历史积累可用性.xlsx', engine='xlsxwriter',
                        engine_kwargs={'options': {'strings_to_urls': False}}) as writer:
        data_result.to_excel(writer, index=False)


if __name__ == '__main__':
    main()

