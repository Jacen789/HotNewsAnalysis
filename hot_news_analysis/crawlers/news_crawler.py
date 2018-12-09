# -*- coding:utf-8 -*-

import urllib.request
import json
import re
import lxml.html
from lxml import etree
import random
from datetime import datetime
import pandas as pd

LATEST_COLS = ['title', 'time', 'url']
LATEST_COLS_C = ['title', 'time', 'url', 'content']

sina_template_url = 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num={}&page={}&r={}'
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
    'sina': '//*[@id="artibody" or @id="article"]//p',
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
        request = urllib.request.Request(url, headers=headers)
        opener = urllib.request.build_opener()
        text = opener.open(request).read().decode('utf-8')
        html = lxml.etree.HTML(text)
        res = html.xpath(xpaths[net])
        p_str_list = [etree.tostring(node).strip().decode('utf-8') for node in res]
        content = '\n'.join(p_str_list)
        html_content = lxml.html.fromstring(content)
        content = html_content.text_content()
        content = re.sub(r'\s*\n\s*', '\n', content)
        content = re.sub(r'\s(\s)', r'\1', content)
        content = content.strip()
    except Exception as e:
        print(e)
    return content


def get_sina_latest_news(template_url, top=80, show_content=False):
    """获取新浪即时财经新闻"""
    try:
        num_list = [50] * (top // 50)
        last_page_num = top % 50
        if last_page_num:
            num_list += [last_page_num]

        df_data = []
        for page, num in enumerate(num_list, start=1):
            r = random.random()
            url = template_url.format(50, page, r)
            print(url)
            request = urllib.request.Request(url, headers=headers)
            data_str = urllib.request.urlopen(request, timeout=10).read()
            response_dict = json.loads(data_str)
            data_list = response_dict['result']['data']

            for data in data_list[:num]:
                ctime = datetime.fromtimestamp(int(data['ctime']))
                ctime = datetime.strftime(ctime, '%Y-%m-%d %H:%M')
                url = data['url']
                row = [data['title'], ctime, url]
                if show_content:
                    row.append(latest_content('sina', url))
                df_data.append(row)
        df = pd.DataFrame(df_data, columns=LATEST_COLS_C if show_content else LATEST_COLS)
        return df
    except Exception as e:
        print('sina:', e)


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
        print('sohu:', e)


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
        print('xinhuanet:', e)


def save_news(news_df, path):
    """保存新闻"""
    news_df.to_csv(path, index=False, encoding='utf-8')


def replace_line_terminator(x):
    """替换行终止符"""
    try:
        x = re.sub(r'\r\n', '\n', x)
    except TypeError:
        pass
    return x


def load_news(path):
    """加载新闻"""
    news_df = pd.read_csv(path, encoding='utf-8')
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


if __name__ == '__main__':
    df = get_latest_news('xinhuanet', top=10, show_content=True)
    print(df['content'])
