# -*- coding:utf-8 -*-

import pandas as pd
import re
import pickle


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


def save_text(document, path):
    """保存txt文件"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(document)


def load_text(path):
    """加载txt文件"""
    with open(path, 'r', encoding='utf-8') as f:
        document = f.read()
    return document


def save_element(element, path):
    """保存元素"""
    with open(path, 'wb') as f:
        pickle.dump(element, f)


def load_element(path):
    """加载元素"""
    with open(path, 'rb') as f:
        element = pickle.load(f)
    return element
