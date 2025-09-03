import requests
import pandas as pd

class Parser:
    def __init__(self,url,url_type='m3u',delimiter=None):
        self.url=url
        self.url_type=url_type
        self.delimiter=delimiter

    def ger_url(self):
        try:
            data=requests.get(self.url,timeout=10).text
            # print(data)
            return data
        except Exception as e:
            print(f'获取直播源地址：{self.url} 出错，错误信息：{e}')
            return None

    def parse_line_tvg_name(self,line1):
        line1_splits = line1.split(',')[0].split()
        for line1_split in line1_splits:
            if 'tvg-name' in line1_split:
                tvg_name = line1_split.split('=')[1].replace('"', '').replace("'", '')
                return tvg_name
        return None

    def parse_line_group_title(self, line1):
        line1_splits = line1.split(',')[0].split()
        for line1_split in line1_splits:
            if 'group-title' in line1_split:
                group_title = line1_split.split('=')[1].replace('"', '').replace("'", '')
                return group_title
        return None

    def parse_line(self, line1, line2):
        """高效解析M3U直播源行数据"""
        line1 = line1.strip()
        line2 = line2.strip()

        # 早期退出：非EXTINF行直接返回默认值
        if not line1.startswith("#EXTINF:"):
            return self.url, None, None, None, None

        # 提取频道名称（只分割一次提高效率）
        try:
            channel_name = line1.split(',', 1)[1]  # maxsplit=1 避免完整字符串扫描
        except (IndexError, ValueError):
            channel_name = None

        # 统一处理URL类型判断
        if line2.startswith(("http://[", "https://[", "rtp://[")):
            channel_type = 'IPV6'
        elif line2.startswith(("http://", "https://", "rtp://")):
            channel_type = 'IPV4'
        else:
            return self.url, None, channel_name, None, None  # 无效URL格式

        # 统一处理URL
        channel_url = line2
        if pd.notna(self.delimiter) and self.delimiter in channel_url:
            channel_url = channel_url.rsplit(self.delimiter, 1)[0]

        # 统一解析元数据
        channel_group = self.parse_line_group_title(line1)

        # 优化tvg-name检查（避免重复字符串搜索）
        tvg_name = self.parse_line_tvg_name(line1) if 'tvg-name' in line1 else None

        # 返回最终结果（使用短路运算提高可读性）
        return self.url, channel_group, tvg_name or channel_name, channel_url, channel_type

    def parse_m3u(self):
        data=self.ger_url()
        if data:
            lives=data.splitlines()
            length = len(lives)

            cn = 0
            result = []
            while cn < length - 1:
                channel_info = self.parse_line(lives[cn],lives[cn + 1])

                if channel_info[4]:
                    result.append(channel_info)
                    cn += 2
                else:
                    cn += 1

            return result
        else:
            return None


    def parse_txt(self):
        data = self.ger_url()
        if data:
            lives = data.splitlines()
            result = []

            channel_group=''
            for channel in lives:
                channel=channel.strip()
                if channel:
                    if '#genre#' in channel:
                        channel_group=channel.split(',', 1)[0]
                        continue
                    # print(channel)
                    channel_split = channel.split(',', 1)
                    if len(channel_split) == 2:
                        channel_name, channel_url = channel.split(',', 1)
                    else:
                        continue

                    if pd.notna(self.delimiter):
                        channel_url = channel_url.rsplit(self.delimiter, 1)[0]

                    if channel_url.startswith("http://[") or channel_url.startswith("https://["):
                        channel_type = 'IPV6'
                    else:
                        channel_type = 'IPV4'

                    result.append((self.url, channel_group, channel_name, channel_url, channel_type))
            return result

        else:
            return None

    def parse(self):
        if self.url_type=='m3u':
            return self.parse_m3u()
        else:
            return self.parse_txt()

if __name__ == '__main__':
    url='https://raw.githubusercontent.com/alantang1977/iptv_api/refs/heads/main/output/live_ipv6.m3u'
    parser=Parser(url,url_type='m3u',delimiter='$')
    print(parser.parse())
