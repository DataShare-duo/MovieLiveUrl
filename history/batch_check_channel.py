import asyncio
import aiohttp

timeout = aiohttp.ClientTimeout(total=10)

async def async_get_url(url,sem):

    async with sem:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url,timeout=timeout) as r:
                    if r.status == 200:
                        print(url)
            except:
                pass

def gene_urls():
    # ips = ['39.134.24.162', '39.134.24.161', '39.134.24.166']
    urls = []
    for i in range(1, 10000):
        # for ip in ips:
            # url = f"http://{ip}/dbiptv.sn.chinamobile.com/PLTV/88888890/224/322122{i:04}/index.m3u8"
        # url=f"http://111.13.111.242/000000001000PLTV/88888888/224/322123{i:04}/1.m3u8?HlsProfileId="
        url = f"http://[2409:8087:1e03:21::2]:6060/cms001/ch0000009099000000{i:04}/index.m3u8"

        urls.append(url)

    return urls


if __name__=='__main__':

    sem = asyncio.Semaphore(1000)   #协程并发任务量
    tasks = [async_get_url(url, sem) for url in gene_urls()]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
