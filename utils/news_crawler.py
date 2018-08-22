# -*- coding:utf-8 -*-

import urllib.request
import json
import re
import lxml.html
from lxml import etree
from random import randint
from datetime import datetime
import pandas as pd

# 测试所需模块
import os
import threading
import multiprocessing

LATEST_COLS = ['title', 'time', 'url']
LATEST_COLS_C = ['title', 'time', 'url', 'content']

sina_template_url = 'http://roll.news.sina.com.cn/interface/rollnews_ch_out_interface.php' \
                    '?col=43&spec=&type=&ch=03&k=&offset_page=0&offset_num=0&num={}&asc=&page=1&r=0.{}'
sohu_template_url = 'http://v2.sohu.com/public-api/feed?scene=CHANNEL&sceneId=15&page=1&size={}'
xinhuanet_template_url = 'http://qc.wa.news.cn/nodeart/list?nid=11147664&pgnum={}&cnt={}&tp=1&orderby=1'
nets = ['sina', 'sohu', 'xinhuanet']

template_urls = {
    'sina': sina_template_url,
    'sohu': sohu_template_url,
    'xinhuanet': xinhuanet_template_url
}
most_top = {
    'sina': 6000,
    'sohu': 1000,
    'xinhuanet': 1000
}
latest_news_functions = {
    'sina': 'get_sina_latest_news',
    'sohu': 'get_sohu_latest_news',
    'xinhuanet': 'get_xinhuanet_latest_news'
}
xpaths = {
    'sina': '//*[@id="artibody"]/p',
    'sohu': '//*[@id="mp-editor"]/p',
    'xinhuanet': '//*[@id="p-detail"]/p'
}

user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36'
headers = {'User-agent': user_agent}


def get_latest_news(net, top=80, show_content=False):
    """
    获取即时财经新闻（新浪、搜狐、新华网）
    :param net: string，指定网站名
    :param top: 数值，显示最新消息的条数，默认为80条
    :param show_content: 是否显示新闻内容，默认False
    :return: DataFrame
        title: 新闻标题
        time: 发布时间
        url: 新闻链接
        content: 新闻内容（在show_content为True的情况下出现）
    """
    assert net in nets, '参数1(net)错误！应为' + '、'.join(nets) + '中的一个！'
    most_top_num = most_top[net]
    assert top > 0, 'top <= 0'
    if top > most_top_num:
        print('top>{}，将获取{}条即时财经新闻'.format(most_top_num, most_top_num))
        top = most_top_num
    latest_news_function = latest_news_functions[net]
    template_url = template_urls[net]
    df = eval('{}(\'{}\',{},{})'.format(latest_news_function, template_url, top, show_content))
    return df


def latest_content(net, url):
    """
    获取即时财经新闻内容
    :param net: 指定网站名
    :param url: 新闻链接
    :return: string
        返回新闻的文字内容
    """
    content = ''
    try:
        html = lxml.html.parse(url, parser=etree.HTMLParser(encoding='utf-8'))
        res = html.xpath(xpaths[net])
        p_str_list = [etree.tostring(node).strip().decode('utf-8') for node in res]
        content = '\n'.join(p_str_list)
        html_content = lxml.html.fromstring(content)
        content = html_content.text_content()
        content = re.sub(r'(\r*\n)+', '\n', content)
    except Exception as e:
        print(e)
    return content


def get_sina_latest_news(template_url, top=80, show_content=False):
    """获取新浪即时财经新闻"""
    try:
        url = template_url.format(top, randint(10 ** 15, (10 ** 16) - 1))
        print(url)
        request = urllib.request.Request(url, headers=headers)
        data_str = urllib.request.urlopen(request, timeout=10).read()
        data_str = data_str.decode('gbk')
        data_str = data_str.split('=', 1)[1][:-1]
        data_str = eval(data_str, type('Dummy', (dict,), dict(__getitem__=lambda s, n: n))())
        data_str = json.dumps(data_str)
        data_str = json.loads(data_str)
        data_str = data_str['list']
        data = []
        for r in data_str:
            rt = datetime.fromtimestamp(r['time'])
            rt_str = datetime.strftime(rt, '%Y-%m-%d %H:%M')
            row = [r['title'], rt_str, r['url']]
            if show_content:
                row.append(latest_content('sina', r['url']))
            data.append(row)
        df = pd.DataFrame(data, columns=LATEST_COLS_C if show_content else LATEST_COLS)
        return df
    except Exception as e:
        print(e)


def get_sohu_latest_news(template_url, top=80, show_content=False):
    """获取搜狐即时财经新闻"""
    try:
        url = template_url.format(top)
        print(url)
        request = urllib.request.Request(url, headers=headers)
        data_str = urllib.request.urlopen(request, timeout=10).read()
        data_str = data_str.decode('utf-8')
        data_str = data_str[1:-1]
        data_str = eval(data_str, type('Dummy', (dict,), dict(__getitem__=lambda s, n: n))())
        data_str = json.dumps(data_str)
        data_str = json.loads(data_str)
        data = []
        for r in data_str:
            rt = datetime.fromtimestamp(r['publicTime'] // 1000)
            rt_str = datetime.strftime(rt, '%Y-%m-%d %H:%M')
            r_url = 'http://www.sohu.com/a/' + str(r['id']) + '_' + str(r['authorId'])
            row = [r['title'], rt_str, r_url]
            if show_content:
                row.append(latest_content('sohu', r_url))
            data.append(row)
        df = pd.DataFrame(data, columns=LATEST_COLS_C if show_content else LATEST_COLS)
        return df
    except Exception as e:
        print(e)


def get_xinhuanet_latest_news(template_url, top=80, show_content=False):
    """获取新华网即时财经新闻"""
    try:
        num = top
        pgnum = 1
        data = []
        while num / 200 > 0:
            cnt = (num - 1) % 200 + 1
            url = template_url.format(pgnum, cnt)
            print(url)
            pgnum += 1
            num -= cnt
            request = urllib.request.Request(url, headers=headers)
            data_str = urllib.request.urlopen(request, timeout=10).read()
            data_str = data_str.decode('utf-8')
            data_str = data_str[1:-1]
            data_str = eval(data_str, type('Dummy', (dict,), dict(__getitem__=lambda s, n: n))())
            data_str = json.dumps(data_str)
            data_str = json.loads(data_str)
            data_str = data_str['data']['list']
            for r in data_str:
                rt = datetime.strptime(r['PubTime'], '%Y-%m-%d %H:%M:%S')
                rt_str = datetime.strftime(rt, '%Y-%m-%d %H:%M')
                row = [r['Title'], rt_str, r['LinkUrl']]
                if show_content:
                    row.append(latest_content('xinhuanet', r['LinkUrl']))
                data.append(row)
        df = pd.DataFrame(data, columns=LATEST_COLS_C if show_content else LATEST_COLS)
        return df
    except Exception as e:
        print(e)


def save_news(news_df, path):
    """保存新闻"""
    news_df.to_csv(path, index=False, encoding='gb18030')


def replace_line_terminator(x):
    """替换行终止符"""
    try:
        x = re.sub(r'\r\n', '\n', x)
    except TypeError:
        pass
    return x


def load_news(path):
    """加载新闻"""
    news_df = pd.read_csv(path, encoding='gb18030')
    news_df = news_df.applymap(replace_line_terminator)
    return news_df


def sina_crawler(top, path):
    """
    新浪爬虫
    爬取最新的top条新浪新闻，并保存在news目录下
    """
    if top <= 0:
        return
    sina_news_df = get_latest_news('sina', top=top, show_content=True)
    print('sina_news_df.shape=', sina_news_df.shape)
    save_news(sina_news_df, path)


def sohu_crawler(top, path):
    """
    搜狐爬虫
    爬取最新的top条搜狐新闻，并保存在news目录下
    """
    if top <= 0:
        return
    sohu_news_df = get_latest_news('sohu', top=top, show_content=True)
    print('sohu_news_df.shape=', sohu_news_df.shape)
    save_news(sohu_news_df, path)


def xinhuanet_crawler(top, path):
    """
    新华网爬虫
    爬取最新的top条新华网新闻，并保存在news目录下
    """
    if top <= 0:
        return
    xinhuanet_news_df = get_latest_news('xinhuanet', top=top, show_content=True)
    print('xinhuanet_news_df.shape=', xinhuanet_news_df.shape)
    save_news(xinhuanet_news_df, path)


"""-------------------------测试代码-------------------------"""

file_dir_path = os.path.dirname(os.path.realpath(__file__))  # 当前文件所在目录路径
news_path = os.path.join(os.path.dirname(file_dir_path), 'data', 'news')  # 新闻存储的目录路径
sina_latest_news_path = os.path.join(news_path, 'sina_latest_news.csv')
sohu_latest_news_path = os.path.join(news_path, 'sohu_latest_news.csv')
xinhuanet_latest_news_path = os.path.join(news_path, 'xinhuanet_latest_news.csv')


def threaded_crawler(sina_top=10, sohu_top=10, xinhuanet_top=10):
    """多线程爬虫"""
    thread1 = threading.Thread(target=sina_crawler, args=(sina_top, sina_latest_news_path))
    thread2 = threading.Thread(target=sohu_crawler, args=(sohu_top, sohu_latest_news_path))
    thread3 = threading.Thread(target=xinhuanet_crawler, args=(xinhuanet_top, xinhuanet_latest_news_path))
    thread1.start()
    thread2.start()
    thread3.start()
    threads = [thread1, thread2, thread3]
    for thread in threads:
        thread.join()
    print('爬取新闻完成！')


def process_crawler(sina_top=10, sohu_top=10, xinhuanet_top=10):
    """多进程爬虫"""
    p1 = multiprocessing.Process(target=sina_crawler, args=(sina_top, sina_latest_news_path))
    p2 = multiprocessing.Process(target=sohu_crawler, args=(sohu_top, sohu_latest_news_path))
    p3 = multiprocessing.Process(target=xinhuanet_crawler, args=(xinhuanet_top, xinhuanet_latest_news_path))
    p1.start()
    p2.start()
    p3.start()
    processes = [p1, p2, p3]
    for p in processes:
        p.join()
    print('爬取新闻完成！')


if __name__ == '__main__':
    threaded_crawler(10, 10, 10)
    # process_crawler(10, 10, 10)
