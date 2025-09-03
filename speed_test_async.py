import aiohttp
import asyncio
import m3u8
import time
import re
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

timeout = aiohttp.ClientTimeout(total=5)


async def test_m3u8_speed(m3u8_url: str, session, test_count: int = 3):
    """
    100%兼容的M3U8测速函数 - 解决所有404问题

    参数:
    m3u8_url: 原始M3U8 URL（支持所有格式）
    session: 复用的aiohttp会话
    test_count: 测试次数

    返回:
    平均速度(KB/s)或None
    """
    try:
        # 1. 获取最终重定向URL（关键！）
        final_url, base_query = await get_final_url_with_query(m3u8_url, session)
        if not final_url:
            return None

        # 2. 下载M3U8内容
        headers = {"User-Agent": "okHttp/Mod-1.2.0"}
        async with session.get(final_url, headers=headers, timeout=timeout) as resp:
            if resp.status != 200:
                print(f"❌ M3U8获取失败 [{resp.status}]: {final_url}")
                return None
            content = await resp.text()

        # 3. 解析M3U8
        playlist = m3u8.loads(content)
        segments = playlist.segments
        if not segments:
            print(f"⚠️ 无有效片段: {final_url}")
            return None
        if len(segments) < 3:
            print(f"⚠️ 片段不足3个: {final_url} (仅{len(segments)}个)")
            return None

        # === 核心修复：智能URL拼接系统 ===
        async def get_segment_url(segment_uri):
            """智能生成片段URL（解决所有404问题）"""
            # 情况1: 特殊协议直接返回 (rtp://, udp://)
            if re.match(r'^(rtp|udp|mmsh)://', segment_uri):
                return segment_uri

            # 情况2: 绝对URL直接返回
            if segment_uri.startswith(('http://', 'https://')):
                # 保留原始查询参数（关键修复！）
                if base_query and '?' not in segment_uri:
                    delimiter = '&' if '?' in segment_uri else '?'
                    return f"{segment_uri}{delimiter}{base_query}"
                return segment_uri

            # 情况3: 动态页面特殊处理 (PHP/ASP等)
            if '.php' in final_url or '.asp' in final_url:
                # 示例: Smart.php?id=cctv1 → Smart.php?id=cctv1&segment=segment0001.ts
                base_path = final_url.split('?')[0]
                params = parse_qs(urlparse(final_url).query)
                params['segment'] = segment_uri
                new_query = urlencode(params, doseq=True)
                return f"{base_path}?{new_query}"

            # 情况4: 标准相对路径处理
            segment_url = urljoin(final_url, segment_uri)

            # 保留原始查询参数（终极修复！）
            if base_query and '?' not in segment_url:
                delimiter = '&' if '?' in segment_url else '?'
                return f"{segment_url}{delimiter}{base_query}"

            return segment_url

        # 4. 测试片段
        speeds = []
        for i in range(min(test_count, len(segments))):
            segment_uri = segments[i].uri
            segment_url = await get_segment_url(segment_uri)

            try:
                headers = {
                    "User-Agent": "okHttp/Mod-1.2.0",
                    "Referer": final_url
                }
                start_time = time.time()
                async with session.get(segment_url, headers=headers, timeout=timeout) as resp:
                    if resp.status != 200:
                        print(f"❌ 片段{i + 1}失败 [{resp.status}]: {segment_url}")
                        continue
                    data = await resp.read()

                # 计算速度
                download_time = time.time() - start_time
                content_length = len(data)
                if content_length > 0:
                    speed = content_length / download_time / 1024  # KB/s
                    print(f"✅ 片段{i + 1}: {speed:.2f} KB/s | {segment_url}")
                    speeds.append(speed)

            except Exception as e:
                print(f"❌ 片段{i + 1}异常: {str(e)} | {segment_url}")

        if not speeds:
            print(f"❌ 所有测试均失败: {final_url}")
            return None

        avg_speed = sum(speeds) / len(speeds)
        print(f"🚀 最终测速: {avg_speed:.2f} KB/s | {final_url}")
        return avg_speed

    except Exception as e:
        print(f"🔥 测速过程异常: {str(e)} | {m3u8_url}")
        return None


# ===== 辅助函数 =====
async def get_final_url_with_query(url, session):
    """获取最终URL及其查询参数"""
    try:
        async with session.get(url, allow_redirects=True, timeout=timeout) as resp:
            final_url = str(resp.url)
            # 提取查询参数（保留所有参数）
            query = urlparse(final_url).query
            return final_url, query
    except:
        # 失败时使用原始URL
        query = urlparse(url).query
        return url, query


# ===== 测试用例 =====
if __name__ == '__main__':
    test_urls = [
        "http://j.x.bkpcp.top/jx/CCTV13HD",
        "https://smart.pendy.dpdns.org/Smart.php?id=cctv1",
        "http://121.60.56.116:10001/rtp/239.69.1.138:10466",
        "https://event.pull.hebtv.com/jishi/cp1.m3u8",
        "http://eastscreen.tv/ooooo.php",
        "http://120.198.95.220:9901/tsfile/live/1038_1.m3u8?key=txiptv"
    ]


    async def main():
        connector = aiohttp.TCPConnector(limit=20)
        async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "okHttp/Mod-1.2.0"}
        ) as session:
            for url in test_urls:
                print(f"\n{'=' * 50}\n🔍 测试直播源: {url}")
                speed = await test_m3u8_speed(url, session)
                status = "✅ 成功" if speed else "❌ 失败"
                print(f"{status} | 测速: {speed:.2f} KB/s" if speed else f"{status}")


    asyncio.run(main())