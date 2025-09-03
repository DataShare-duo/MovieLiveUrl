import requests
import time
import m3u8
from urllib.parse import urljoin, urlparse


def test_m3u8_speed(m3u8_url, test_count=3):
    """
    测试M3U8直播源的速度
    
    参数:
    m3u8_url: M3U8直播源的URL
    test_count: 测试次数，默认为3次
    
    返回:
    平均速度(KB/s)，如果测试失败则返回None
    """
    speeds = []
    
    try:
        # 加载M3U8文件
        playlist = m3u8.load(m3u8_url)
        segments = playlist.segments
        
        if not segments:
            print("错误: M3U8文件中没有找到视频段")
            return None
        
        # 构建基础URL（处理相对路径）
        parsed_uri = urlparse(m3u8_url)
        base_uri = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        
        for i in range(test_count):
            # 选择一个视频段（循环使用可用段）
            segment = segments[i % len(segments)]
            segment_uri = segment.uri
            
            # 处理相对URL
            if segment_uri.startswith('http'):
                segment_url = segment_uri
            elif segment_uri.startswith('/'):
                segment_url = base_uri + segment_uri
            else:
                # 对于相对路径，使用M3U8文件所在目录作为基础
                base_url = m3u8_url.rsplit('/', 1)[0] + '/'
                segment_url = urljoin(base_url, segment_uri)
            
            # 测试下载速度
            try:
                start_time = time.time()
                response = requests.get(segment_url, stream=True, timeout=5)
                if response.status_code != 200:
                    return None
                # 获取内容长度
                content_length = len(response.content)
                if content_length:
                    # 计算下载速度
                    download_time = time.time() - start_time
                    speed = content_length / download_time / 1024  # KB/s
                    speeds.append(speed)
                    
                    print(f"测试 {i+1}: 速度 {speed:.2f} KB/s")
                else:
                    return None
                
            except Exception as e:
                print(f"测试 {i+1} 失败: {str(e)}")
                continue
        
        if not speeds:
            print("所有测试都失败了")
            return None
        
        # 计算平均速度
        avg_speed = sum(speeds) / len(speeds)
        print(f"平均速度: {avg_speed:.2f} KB/s")
        return avg_speed
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        return None
        
        
        