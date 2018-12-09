# -*- coding: utf-8 -*-

import re
import jieba
import jieba.posseg as pseg
import json
from datetime import datetime
from datetime import timedelta


def data_filter(df):
    """数据过滤"""
    # 过滤掉没有内容的新闻
    df = df[df['content'] != ''].copy()
    df = df.dropna(subset=['content']).copy()
    # 去重
    df = df.drop_duplicates(subset=['url'])
    df = df.drop_duplicates(subset=['title'])
    df = df.reset_index(drop=True)
    return df


def get_data(df, last_time, delta):
    """
    获取某段时间的新闻数据
    :param df: 原始数据
    :param last_time: 指定要获取数据的最后时间
    :param delta: 时间间隔
    :return: last_time前timedelta的数据
    """
    last_time = datetime.strptime(last_time, '%Y-%m-%d %H:%M')
    delta = timedelta(delta)
    try:
        df['time'] = df['time'].map(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M'))
    except TypeError:
        pass
    df = df[df['time'].map(lambda x: (x <= last_time) and (x > last_time - delta))].copy()
    print('df.shape=', df.shape)
    if df.shape[0] == 0:
        print('No Data!')
        return df
    df = df.sort_values(by=['time'], ascending=[0])
    df['time'] = df['time'].map(lambda x: datetime.strftime(x, '%Y-%m-%d %H:%M'))
    df = df.reset_index(drop=True)
    return df


def clean_title_blank(title):
    """清理新闻标题空白"""
    # 清理未知字符
    title = re.sub(r'\?+', ' ', title)
    # 清理空白字符
    title = re.sub(r'\u3000', '', title)
    title = title.strip()
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'([|：])+ ', r'\1', title)
    title = re.sub(r' ([|：])+', r'\1', title)
    return title


def clean_content_blank(content):
    """清理新闻内容空白"""
    # 清理未知字符
    content = re.sub(r'\?+', ' ', content)
    # 清理空白字符
    content = re.sub(r'\u3000', '', content)
    content = content.strip()
    content = re.sub(r'[ \t\r\f]+', ' ', content)
    content = re.sub(r'\n ', '\n', content)
    content = re.sub(r' \n', '\n', content)
    content = re.sub(r'\n+', '\n', content)
    return content


def clean_content(content):
    """清理新闻内容"""
    # 清理新闻内容空白
    content = clean_content_blank(content)
    # 英文大写转小写
    content = content.lower()
    # 清理超链接
    content = re.sub(r'https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]', '', content)
    # 清理责任编辑等
    content = re.split(r'\n责任编辑', content)[0]
    content = re.split(r'返回搜狐，查看更多', content)[0]
    # 清理原标题
    content = re.sub(r'原标题：.*\n', '', content)
    # 清理来源等和内容无关的文字
    texts = [
        r'新浪财经讯[ ，]*', r'新浪美股讯[ ，]*', r'新浪外汇讯[ ，]*', r'新浪科技讯[ ，]*',
        r'[（\(].{,10}来源[:：].{,30}[）\)]',
        r'(?<=\n).{,2}来源[:：].{,30}\n', r'(?<=\n).{,2}来源[:：].{,30}$',
        r'[（\(].{,20}记者[ :：].{,20}[）\)]',
        r'(?<=\n).{,2}作者：.{,20}\n', r'(?<=\n).{,2}作者：.{,20}$',
        r'(?<=\n).{,2}编辑：.{,20}\n', r'(?<=\n).{,2}编辑：.{,20}$'
    ]
    for text in texts:
        content = re.sub(text, '', content)
    content = re.sub(r'\n+', '\n', content)
    return content


def get_num_en_ch(text):
    """提取数字英文中文"""
    text = re.sub(r'[^0-9A-Za-z\u4E00-\u9FFF]+', ' ', text)
    text = text.strip()
    return text


def pseg_cut(text, userdict_path=None):
    """
    词性标注
    :param text: string，原文本数据
    :param userdict_path: string，用户词词典路径，默认为None
    :return: list， 分词后词性标注的列表
    """
    if userdict_path is not None:
        jieba.load_userdict(userdict_path)
    words = pseg.lcut(text)
    return words


def get_words_by_flags(words, flags=None):
    """
    获取指定词性的词
    :param words: list， 分词后词性标注的列表
    :param flags: list， 词性标注，默认为提取名词和动词
    :return: list， 指定词性的词
    """
    flags = ['n.*', 'v.*'] if flags is None else flags
    words = [w for w, f in words if w != ' ' and re.match('|'.join(['(%s$)' % flag for flag in flags]), f)]
    return words


def userdict_cut(text, userdict_path=None):
    """
    对文本进行jieba分词
    如果使用用户词词典，那么使用用户词词典进行jieba分词
    """
    if userdict_path is not None:
        jieba.load_userdict(userdict_path)
    words = jieba.cut(text)
    return words


def stop_words_cut(words, stop_words_path):
    """停用词处理"""
    with open(stop_words_path, 'r', encoding='utf-8') as f:
        stopwords = [line.strip() for line in f.readlines()]
        stopwords.append(' ')
        words = [word for word in words if word not in stopwords]
    return words


def disambiguation_cut(words, disambiguation_dict_path):
    """消歧词典"""
    with open(disambiguation_dict_path, 'r', encoding='utf-8') as f:
        disambiguation_dict = json.load(f)
        words = [(disambiguation_dict[word]
                  if disambiguation_dict.get(word) else word) for word in words]
    return words


def individual_character_cut(words, individual_character_dict_path):
    """删除无用单字"""
    with open(individual_character_dict_path, 'r', encoding='utf-8') as f:
        individual_character = [line.strip() for line in f.readlines()]
        words = [word for word in words
                 if ((len(word) > 1) or ((len(word) == 1) and (word in individual_character)))]
    return words


def document2txt(raw_document, userdict_path, text_path):
    """文本分词并保存为txt文件"""
    document = clean_content_blank(raw_document)
    document = document.lower()
    document_cut = userdict_cut(document, userdict_path)
    result = ' '.join(document_cut)
    result = re.sub(r' +', ' ', result)
    result = re.sub(r' \n ', '\n', result)
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(result)
