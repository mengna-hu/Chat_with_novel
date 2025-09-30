import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import random
import csv
import re
import os
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


# 设置请求头，模拟浏览器访问
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive'
}

# 设置请求延迟范围（秒），避免请求过于频繁
MIN_DELAY = 2
MAX_DELAY = 5

def get_novel_list_from_rank(page_num, cookies=None):
    """
    从晋江收藏排行榜获取指定页码的小说列表信息
    """
    proxy = {"http":"http://代理的IP地址:端口号", "https":"https://代理的IP地址:端口号"}
    rank_url = f"http://www.jjwxc.net/bookbase.php?fw0=0&fbsj0=0&ycx0=0&xx0=0&mainview0=0&sd0=0&lx0=0&fg0=0&bq=-1&sortType=4&isfinish=0&collectiontypes=ors&page={page_num}"
    
    try:
        # proxies = proxy
        response = requests.get(rank_url, headers=HEADERS, cookies=cookies)
        response.encoding = 'gbk'
        
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # print("soup:", soup)
        novel_list = []
        
        # 查找包含小说信息的表格行
        for tr in soup.find_all('tr'):
            cells = tr.find_all('td')

            link_td = tr.find('td', align="left")
            if not link_td:
                continue

            # 提取小说详情页链接
            link_tag = tr.find('a', href=re.compile(r'onebook\.php\?novelid=\d+'))
            if not link_tag:
                continue
                
            novel_url = urljoin("http://www.jjwxc.net/", link_tag['href'])
            novel_name = link_tag.get_text(strip=True)
            
            # 提取作者信息
            author_td = tr.find('td', align="left")
            author_tag = author_td.find('a', href=re.compile(r'oneauthor\.php\?authorid=\d+'))
            author = author_tag.get_text(strip=True) if author_tag else "未知"
            
            novel_title = cells[1].find('a').get('title', '') if cells[1].find('a') else ''
            # 从title属性中提取简介和标签
            if novel_title:
                # 分割简介和标签部分
                parts = novel_title.split('标签：')
                # 提取简介
                introduction = parts[0].replace('简介：', '').strip()
                # 提取标签
                tags = parts[1] if len(parts) > 1 else []
            else:
                introduction = ''
                tags = ''

            # 3. 分类信息
            novel_type = cells[2].get_text(strip=True)
            
            # 4. 状态信息
            status_tag = cells[3].find('font')
            status = status_tag.get_text(strip=True) if status_tag else cells[3].get_text(strip=True)
            
            # 5. 字数/点击量
            word_count = cells[4].get_text(strip=True)
            
            # 6. 积分/收藏数
            point = cells[5].get_text(strip=True)
            
            # 7. 发布日期
            publish_date = cells[6].get_text(strip=True)

            
            novel_list.append({
                '书名': novel_name,
                '简介': introduction,
                '标签': tags,
                '链接': novel_url,
                '作者': author,
                '类型': novel_type,
                '字数': word_count,
                '完结状态': status,
                "积分": point,
                "发表时间": publish_date
            })
            
        return novel_list
    except Exception as e:
        print(f"获取第{page_num}页小说列表时出错: {e}")
        return []

def get_novel_detail(novel_url):
    """
    从小说详情页提取具体信息
    """
    # 定义重试策略
    retry_strategy = Retry(
        total=3,  # 最大重试次数（包括第一次请求）
        backoff_factor=0.5,  # 退避因子，用于计算重试间隔时间 (例如 0.5 -> 0.5s, 1.0s, 2.0s)
        status_forcelist=[429, 500, 502, 503, 504],  # 遇到这些状态码会强制重试
        # 429 (Too Many Requests) 通常表示需要稍后再试
        # 500系列通常是服务器内部错误，重试可能会成功
        allowed_methods=["GET", "POST"]  # 只对这些HTTP方法重试
    )
    
    # 创建适配器并挂载到 Session
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        response = session.get(novel_url, headers=HEADERS, timeout=10)
        response.encoding = 'gbk'
        
        if response.status_code != 200:
            print(f"小说页面请求失败，状态码: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        novel_intro_div = soup.find('div', id='novelintro')
        if not novel_intro_div:
            print("未找到文章介绍")
        introduction = novel_intro_div.get_text()
        statistics = {}
        statistics["文案"] = introduction

        # correspond = {"totalClick":"非v章节章均点击数", "reviewCount":"总书评数", "collectedCount":"当前被收藏数", "nutritionCount":"营养液数"}
        # table = soup.find('table', id="oneboolt")
        # if table:
        #     last_row = table.find_all("tr")[-1]
        #     spans = last_row.find_all('span')
        #     print(spans)
        #     for span in spans:
        #         itemprop = span.get('itemprop')
        #         if itemprop in correspond.keys():
        #             value = span.get_text(strip=True)
        #             statistics[correspond[itemprop]] = value
        
        return statistics
    except Exception as e:
        print(f"解析小说详情页 {novel_url} 时出错: {e}")
        return None
    finally:
        session.close()  #

def process_novel(novel):
    """处理单本小说的函数，用于并行执行"""
    print(f"正在爬取小说: {novel['书名']}")
    novel_detail = get_novel_detail(novel['链接'])
    
    if novel_detail:
        novel.update(novel_detail)
    
    # 设置随机延迟，避免请求过于频繁
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    time.sleep(delay)
    
    return novel

def save_to_csv(data_list, start_page, end_page):
    """将小说信息列表保存到CSV文件"""
    if not data_list:
        print("没有数据可保存")
        return
    
    filename = 'jjwxc_novels'+'_'+str(start_page)+"_to_"+str(end_page)+'.csv'
    
    keys = data_list[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8-sig') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data_list)
    print(f"数据已保存到 {filename}")

def crawl_jjwxc_novels(start_page=1, end_page=3, max_workers=5):
    """
    爬取晋江文学城小说信息的主函数
    
    :param start_page: 起始页码
    :param end_page: 结束页码
    :param output_file: 输出文件名
    """
    all_novels_info = []
    # cookies = None
    cookies_str = "JJEVER=%7B%22shumeideviceId%22%3A%22WHJMrwNw1k/F+joyefyRjlx2DLH9S1o9T5mw0j00MMxl1Ll9Q3tcqVewydILIK+wJKcteo6XKD2U+JVIYMELI0cX+rrRGSegmdCW1tldyDzmQI99+chXEijZH8Y+bazby9lCUKKcsmkSqmJzoPeggwzYmmmXo8LlTkQE5YcNLqNo1CXZrYdSBTkKAtkFT+Pz4Ty6C61zgOfVMXmJGO84EEsFmp/zKOHGSgFx2O1XlKpEdbreakUja5A%3D%3D1487582755342%22%2C%22fenzhan%22%3A%22yq%22%2C%22nicknameAndsign%22%3A%221%257E%2529%2524%22%2C%22foreverreader%22%3A%2280218467%22%2C%22desid%22%3A%220gti6Zt5ieU281JXmYoScocvn4Bbg+hR%22%2C%22sms_total%22%3A3%2C%22lastCheckLoginTimePc%22%3A1758704775%7D; smidV2=20250924112950a62e87c8592a58c118695e47a316e053007d2854c1c4a66f0; Hm_lpvt_bc3b748c21fe5cf393d26c12b2c38d99=1758704715; Hm_lvt_bc3b748c21fe5cf393d26c12b2c38d99=1758684591; bbsnicknameAndsign=1%257E%2529%2524; bbstoken=ODAyMTg0NjdfMF85MTgyY2I0MzdmMTVmYTQ4ZDE1NjJjMmY5MGE4ZTgwMl8xX19fMQ%3D%3D; token=ODAyMTg0Njd8YTZkNTNmZDRkNWJhZDI3NjRlMTQ0YzRjYjgzMDY1Nzl8fHx8MTI5NjAwfDF8fHzmmYvmsZ%2FnlKjmiLd8MHxtb2JpbGV8MXwwfHw%3D; JJSESS=%7B%22clicktype%22%3A%22%22%2C%22register_info%22%3A%22176ab1cf361652e460ffb83118afbc58%22%2C%22userinfoprocesstoken%22%3A%22%22%2C%22sidkey%22%3A%22Yequ9VwsWUGc0ro8mCAjOnypSi7Z5Q6MPl3EH%22%7D; timeOffset_o=-467.89990234375; HMACCOUNT=2046F5E03F085549; testcookie=yes"
    cookies = {}
    for item in cookies_str.split(';'):
        # 处理可能存在的空格和空值
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    # 如果需要爬取10页之后的内容，需要提供登录后的cookies
    
    print(f"开始爬取晋江文学城小说信息，从第{start_page}页到第{end_page}页...")
    
    for page_num in range(start_page, end_page + 1):
        print(f"正在获取第 {page_num} 页的小说列表...")
        novel_list = get_novel_list_from_rank(page_num, cookies=cookies)

        if not novel_list:
            print(f"第 {page_num} 页未获取到小说列表，可能已到达末尾或需要登录。")
            break
        
        print(f"第 {page_num} 页找到 {len(novel_list)} 本小说")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_novel = {executor.submit(process_novel, novel): novel for novel in novel_list}
            
            # 处理完成的结果
            for future in as_completed(future_to_novel):
                try:
                    result = future.result()
                    all_novels_info.append(result)
                except Exception as e:
                    print(f"处理小说时出错: {e}")
        
        # 每爬完一页也稍作延迟
        time.sleep(random.uniform(1, 3))
    
    # 保存数据
    if all_novels_info:
        save_to_csv(all_novels_info, start_page, end_page)
        print(f"爬取完成！共爬取 {len(all_novels_info)} 本小说信息。")
    else:
        print("未爬取到任何小说信息。")

if __name__ == '__main__':
    start = 101
    end = 1000
    for i in range(start, end, 10):
        crawl_jjwxc_novels(start_page=i, end_page=i+9, max_workers=15)
