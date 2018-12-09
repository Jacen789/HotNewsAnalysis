#  -*- coding: utf-8 -*-

import os
import threading
import pandas as pd

from news_crawler import sina_crawler
from news_crawler import sohu_crawler
from news_crawler import xinhuanet_crawler
from news_crawler import load_news
from news_crawler import save_news


def threaded_crawler(sina_top=10, sohu_top=10, xinhuanet_top=10, save_file_path=None):
    """多线程爬虫"""
    if not save_file_path:
        current_folder_path = os.path.dirname(os.path.abspath(__file__))  # 当前文件所在目录路径
        save_folder_path = os.path.join(current_folder_path, 'news')  # 新闻存储的目录路径
        save_file_path = os.path.join(save_folder_path, 'news_df.csv')
        if not os.path.exists(save_folder_path):
            os.mkdir(save_folder_path)
    else:
        save_folder_path = os.path.dirname(save_file_path)
    sina_latest_news_path = os.path.join(save_folder_path, 'sina_latest_news.csv')
    sohu_latest_news_path = os.path.join(save_folder_path, 'sohu_latest_news.csv')
    xinhuanet_latest_news_path = os.path.join(save_folder_path, 'xinhuanet_latest_news.csv')
    thread1 = threading.Thread(target=sina_crawler, args=(sina_top, sina_latest_news_path))
    thread2 = threading.Thread(target=sohu_crawler, args=(sohu_top, sohu_latest_news_path))
    thread3 = threading.Thread(target=xinhuanet_crawler, args=(xinhuanet_top, xinhuanet_latest_news_path))
    thread1.start()
    thread2.start()
    thread3.start()
    threads = [thread1, thread2, thread3]
    for thread in threads:
        thread.join()
    sina_news_df = pd.DataFrame()
    sohu_news_df = pd.DataFrame()
    xinhuanet_news_df = pd.DataFrame()
    if sina_top > 0:
        sina_news_df = load_news(os.path.join(save_folder_path, 'sina_latest_news.csv'))
    if sohu_top > 0:
        sohu_news_df = load_news(os.path.join(save_folder_path, 'sohu_latest_news.csv'))
    if xinhuanet_top > 0:
        xinhuanet_news_df = load_news(os.path.join(save_folder_path, 'xinhuanet_latest_news.csv'))
    news_df = pd.concat([sina_news_df, sohu_news_df, xinhuanet_news_df], ignore_index=True)
    print('news_df.shape=', news_df.shape)
    save_news(news_df, save_file_path)
    print('爬取新闻完成！')


if __name__ == '__main__':
    threaded_crawler(10, 10, 10)
