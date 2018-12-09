# -*- coding: utf-8 -*-

import os
import pandas as pd
from datetime import datetime
from crawlers import news_crawler
from crawlers import thread_crawler
from utils import news_pandas
from utils import preprocessing
from utils import modeling
from utils import drawing
from utils import counter

import threading

# 获取项目路径
current_folder_path = os.path.dirname(os.path.realpath(__file__))
# 获取数据存放目录路径
data_path = os.path.join(current_folder_path, 'data')
fonts_path = os.path.join(data_path, 'fonts')
images_path = os.path.join(data_path, 'images')
texts_path = os.path.join(data_path, 'texts')
extra_dict_path = os.path.join(data_path, 'extra_dict')
models_path = os.path.join(data_path, 'models')
news_path = os.path.join(data_path, 'news')
temp_news_path = os.path.join(data_path, 'temp_news')
results_path = os.path.join(data_path, 'results')


def my_crawler():
    """爬取新闻数据"""
    # sina_news_df = news_crawler.get_latest_news('sina', top=1000, show_content=True)
    # sohu_news_df = news_crawler.get_latest_news('sohu', top=1000, show_content=True)
    # xinhuanet_news_df = news_crawler.get_latest_news('xinhuanet', top=100, show_content=True)
    # news_crawler.save_news(sina_news_df, os.path.join(news_path, 'sina_latest_news.csv'))
    # news_crawler.save_news(sohu_news_df, os.path.join(news_path, 'sohu_latest_news.csv'))
    # news_crawler.save_news(xinhuanet_news_df, os.path.join(news_path, 'xinhuanet_latest_news.csv'))
    save_file_path = os.path.join(news_path, 'news_df.csv')
    thread_crawler.threaded_crawler(1000, 1000, 10, save_file_path=save_file_path)


def load_data():
    """加载数据"""
    # sina_news_df = news_crawler.load_news(os.path.join(news_path, 'sample_sina_latest_news.csv'))
    # sohu_news_df = news_crawler.load_news(os.path.join(news_path, 'sample_sohu_latest_news.csv'))
    # xinhuanet_news_df = news_crawler.load_news(os.path.join(news_path, 'sample_xinhuanet_latest_news.csv'))
    # sina_news_df = news_crawler.load_news(os.path.join(news_path, 'sina_latest_news.csv'))
    # sohu_news_df = news_crawler.load_news(os.path.join(news_path, 'sohu_latest_news.csv'))
    # xinhuanet_news_df = news_crawler.load_news(os.path.join(news_path, 'xinhuanet_latest_news.csv'))
    # news_df = pd.concat([sina_news_df, sohu_news_df, xinhuanet_news_df], ignore_index=True)
    save_file_path = os.path.join(news_path, 'news_df.csv')
    news_df = news_pandas.load_news(save_file_path)
    return news_df


def filter_data(news_df):
    """过滤数据"""
    df = preprocessing.data_filter(news_df)
    now_time = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M')
    # now_time = '2018-04-06 23:59'
    df = preprocessing.get_data(df, last_time=now_time, delta=5)
    return df


def title_preprocess(df_title):
    """标题分词处理"""
    df_title['title_'] = df_title['title'].map(lambda x: preprocessing.clean_title_blank(x))
    df_title['title_'] = df_title['title_'].map(lambda x: preprocessing.get_num_en_ch(x))
    df_title['title_cut'] = df_title['title_'].map(lambda x: preprocessing.pseg_cut(
        x, userdict_path=os.path.join(extra_dict_path, 'self_userdict.txt')))
    df_title['title_cut'] = df_title['title_cut'].map(lambda x: preprocessing.get_words_by_flags(
        x, flags=['n.*', '.*n', 'v.*', 's', 'j', 'l', 'i', 'eng']))
    df_title['title_cut'] = df_title['title_cut'].map(lambda x: preprocessing.stop_words_cut(
        x, os.path.join(extra_dict_path, 'self_stop_words.txt')))
    df_title['title_cut'] = df_title['title_cut'].map(lambda x: preprocessing.disambiguation_cut(
        x, os.path.join(extra_dict_path, 'self_disambiguation_dict.json')))
    df_title['title_cut'] = df_title['title_cut'].map(lambda x: preprocessing.individual_character_cut(
        x, os.path.join(extra_dict_path, 'self_individual_character_dict.txt')))
    df_title['title_'] = df_title['title_cut'].map(lambda x: ' '.join(x))
    return df_title


def title_cluster(df, save_df=False):
    """按新闻标题聚类"""
    df_title = df.copy()
    df_title = title_preprocess(df_title)
    word_library_list = counter.get_word_library(df_title['title_cut'])
    single_frequency_words_list = counter.get_single_frequency_words(df_title['title_cut'])
    max_features = len(word_library_list) - len(single_frequency_words_list) // 2
    title_matrix = modeling.feature_extraction(df_title['title_'], vectorizer='CountVectorizer',
                                               vec_args={'max_df': 1.0, 'min_df': 1, 'max_features': max_features})
    title_dbscan = modeling.get_cluster(title_matrix, cluster='DBSCAN',
                                        cluster_args={'eps': 0.4, 'min_samples': 4, 'metric': 'cosine'})
    title_labels = modeling.get_labels(title_dbscan)
    df_title['title_label'] = title_labels
    df_non_outliers = modeling.get_non_outliers_data(df_title, label_column='title_label')
    title_label_num = counter.get_num_of_value_no_repeat(df_non_outliers['title_label'].tolist())
    print('按新闻标题聚类，一共有%d个簇(不包括离群点)' % title_label_num)
    title_rank = modeling.label2rank(title_labels)
    df_title['title_rank'] = title_rank
    for i in range(1, title_label_num + 1):
        df_ = df_title[df_title['title_rank'] == i]
        title_top_list = counter.get_most_common_words(df_['title_cut'], top_n=10)
        print(title_top_list)
    if save_df:
        df_title.drop(['content', 'title_', 'title_label'], axis=1, inplace=True)
        news_crawler.save_news(df_title, os.path.join(results_path, 'df_title_rank.csv'))
    return df_title


def content_preprocess(df_content):
    """新闻内容分词处理"""
    df_content['content_'] = df_content['content'].map(lambda x: preprocessing.clean_content(x))
    df_content['content_'] = df_content['content_'].map(lambda x: preprocessing.get_num_en_ch(x))
    df_content['content_cut'] = df_content['content_'].map(lambda x: preprocessing.pseg_cut(
        x, userdict_path=os.path.join(extra_dict_path, 'self_userdict.txt')))
    df_content['content_cut'] = df_content['content_cut'].map(lambda x: preprocessing.get_words_by_flags(
        x, flags=['n.*', '.*n', 'v.*', 's', 'j', 'l', 'i', 'eng']))
    df_content['content_cut'] = df_content['content_cut'].map(lambda x: preprocessing.stop_words_cut(
        x, os.path.join(extra_dict_path, 'self_stop_words.txt')))
    df_content['content_cut'] = df_content['content_cut'].map(lambda x: preprocessing.disambiguation_cut(
        x, os.path.join(extra_dict_path, 'self_disambiguation_dict.json')))
    df_content['content_cut'] = df_content['content_cut'].map(lambda x: preprocessing.individual_character_cut(
        x, os.path.join(extra_dict_path, 'self_individual_character_dict.txt')))
    df_content['content_'] = df_content['content_cut'].map(lambda x: ' '.join(x))
    return df_content


def content_cluster(df, df_save=False):
    """按新闻内容聚类"""
    df_content = df.copy()
    df_content = content_preprocess(df_content)
    word_library_list = counter.get_word_library(df_content['content_cut'])
    single_frequency_words_list = counter.get_single_frequency_words(df_content['content_cut'])
    max_features = len(word_library_list) - len(single_frequency_words_list) // 2
    content_matrix = modeling.feature_extraction(df_content['content_'], vectorizer='CountVectorizer',
                                                 vec_args={'max_df': 0.95, 'min_df': 1, 'max_features': max_features})
    content_dbscan = modeling.get_cluster(content_matrix, cluster='DBSCAN',
                                          cluster_args={'eps': 0.35, 'min_samples': 4, 'metric': 'cosine'})
    content_labels = modeling.get_labels(content_dbscan)
    df_content['content_label'] = content_labels
    df_non_outliers = modeling.get_non_outliers_data(df_content, label_column='content_label')
    content_label_num = counter.get_num_of_value_no_repeat(df_non_outliers['content_label'].tolist())
    print('按新闻内容聚类，一共有%d个簇(不包括离群点)' % content_label_num)
    content_rank = modeling.label2rank(content_labels)
    df_content['content_rank'] = content_rank
    for i in range(1, content_label_num + 1):
        df_ = df_content[df_content['content_rank'] == i]
        content_top_list = counter.get_most_common_words(df_['content_cut'], top_n=15, min_frequency=1)
        print(content_top_list)
    if df_save:
        df_content.drop(['content_', 'content_label'], axis=1, inplace=True)
        news_crawler.save_news(df_content, os.path.join(results_path, 'df_content_rank.csv'))
    return df_content


def get_wordcloud(df, rank_column, text_list_column):
    """
    按照不同的簇生成每个簇的词云
    :param df: pd.DataFrame，带有排名和分词后的文本列表数据
    :param rank_column: 排名列名
    :param text_list_column: 分词后的文本列表列名
    """
    df_non_outliers = modeling.get_non_outliers_data(df, label_column=rank_column)
    label_num = counter.get_num_of_value_no_repeat(df_non_outliers[rank_column].tolist())
    wordcloud_folder_path = os.path.join(results_path, rank_column)
    if not os.path.exists(wordcloud_folder_path):
        os.mkdir(wordcloud_folder_path)
    for i in range(1, label_num + 1):
        df_ = df[df[rank_column] == i]
        list_ = counter.flat(df_[text_list_column].tolist())
        modeling.list2wordcloud(list_, save_path=os.path.join(wordcloud_folder_path, '%d.png' % i),
                                font_path=os.path.join(fonts_path, 'simhei.ttf'))


def key_content(df, df_save=False):
    """获取摘要"""

    def f(text):
        text = preprocessing.clean_content(text)
        text = modeling.get_key_sentences(text, num=1)
        return text

    df['abstract'] = df['content'].map(f)
    if df_save:
        df.drop(['content'], axis=1, inplace=True)
        news_crawler.save_news(df, os.path.join(results_path, 'df_abstract.csv'))
    return df


def get_key_words():
    df_title = news_crawler.load_news(os.path.join(results_path, 'df_title_rank.csv'))
    df_content = news_crawler.load_news(os.path.join(results_path, 'df_content_rank.csv'))
    df_title['title_cut'] = df_title['title_cut'].map(eval)
    df_content['content_cut'] = df_content['content_cut'].map(eval)
    get_wordcloud(df_content, 'content_rank', 'content_cut')
    df_title_content = df_title.copy()
    df_title_content['content_cut'] = df_content['content_cut']
    df_title_content['content_rank'] = df_content['content_rank']
    df_title_content = modeling.get_non_outliers_data(df_title_content, label_column='title_rank')
    title_rank_num = counter.get_num_of_value_no_repeat((df_title_content['title_rank']))
    for i in range(1, title_rank_num + 1):
        df_i = df_title_content[df_title_content['title_rank'] == i]
        title = '\n'.join(df_i['title'].tolist())
        title = modeling.get_key_sentences(title, num=1)
        print('热点：', title)
        content_rank = [k for k in df_i['content_rank']]
        content_rank = set(content_rank)
        for j in content_rank:
            df_j = df_i[df_i['content_rank'] == j]
            most_commmon_words = counter.get_most_common_words(df_j['content_cut'], top_n=20, min_frequency=5)
            if len(most_commmon_words) > 0:
                print('相关词汇：', most_commmon_words)


def main():
    # # my_crawler()
    news_df = load_data()
    df = filter_data(news_df)
    # title_cluster(df, True)
    # content_cluster(df, True)
    t1 = threading.Thread(target=title_cluster, args=(df, True))
    t2 = threading.Thread(target=content_cluster, args=(df, True))
    t1.start()
    t2.start()
    threads = [t1, t2]
    for t in threads:
        t.join()
    get_key_words()


if __name__ == '__main__':
    main()
