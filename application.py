#  -*- coding: utf-8 -*-

import tkinter as tk
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog

import os
import re
import pandas as pd
from utils import news_crawler
from utils import news_pandas
from utils import preprocessing
from utils import modeling
from utils import drawing
from utils import counter

import platform

sysstr = platform.system()
editor = 'notepad'
if sysstr == 'Windows':
    editor = '"D:Program Files\\gedit\\bin\\gedit.exe"'
elif sysstr == 'Linux':
    editor = 'gedit'

# 获取项目路径
project_path = os.path.dirname(os.path.realpath(__file__))
# 获取数据存放目录路径
data_path = os.path.join(project_path, 'data')
fonts_path = os.path.join(data_path, 'fonts')
images_path = os.path.join(data_path, 'images')
texts_path = os.path.join(data_path, 'texts')
extra_dict_path = os.path.join(data_path, 'extra_dict')
models_path = os.path.join(data_path, 'models')
news_path = os.path.join(data_path, 'news')
temp_news_path = os.path.join(data_path, 'temp_news')
results_path = os.path.join(data_path, 'results')

root = tk.Tk()
# root.option_add("*Font", "Arial 10 bold")
root.geometry("800x600+283+82")
root.title("新闻热点关注问题分析系统")

sum_top_n = tk.StringVar()
filter_n = tk.StringVar()
hot_num = tk.StringVar()

filter_df = pd.DataFrame()
filter_df0 = pd.DataFrame()
df_rank_i = pd.DataFrame()


def crawler():
    sina_top_n = Entry_Sina.get()
    sohu_top_n = Entry_Sohu.get()
    xinhuanet_top_n = Entry_XinhuaNet.get()
    sina_top_n = 0 if sina_top_n == '' else int(sina_top_n)
    sohu_top_n = 0 if sohu_top_n == '' else int(sohu_top_n)
    xinhuanet_top_n = 0 if xinhuanet_top_n == '' else int(xinhuanet_top_n)
    sina_top_n = 0 if sina_top_n <= 0 else sina_top_n
    sohu_top_n = 0 if sohu_top_n <= 0 else sohu_top_n
    xinhuanet_top_n = 0 if xinhuanet_top_n <= 0 else xinhuanet_top_n
    if sina_top_n + sohu_top_n + xinhuanet_top_n == 0:
        messagebox.showinfo('Message', '新闻数量不能全部为非正数！')
        return
    news_crawler.threaded_crawler(sina_top_n, sohu_top_n, xinhuanet_top_n)
    sina_news_df = pd.DataFrame()
    sohu_news_df = pd.DataFrame()
    xinhuanet_news_df = pd.DataFrame()
    if sina_top_n > 0:
        sina_news_df = news_pandas.load_news(os.path.join(news_path, 'sina_latest_news.csv'))
    if sohu_top_n > 0:
        sohu_news_df = news_pandas.load_news(os.path.join(news_path, 'sohu_latest_news.csv'))
    if xinhuanet_top_n > 0:
        xinhuanet_news_df = news_pandas.load_news(os.path.join(news_path, 'xinhuanet_latest_news.csv'))
    news_df = pd.concat([sina_news_df, sohu_news_df, xinhuanet_news_df], ignore_index=True)
    news_pandas.save_news(news_df, os.path.join(news_path, 'news_df.csv'))
    global filter_df
    filter_df = preprocessing.data_filter(news_df)
    news_pandas.save_news(filter_df, os.path.join(temp_news_path, 'filter_news.csv'))
    news_num = filter_df.shape[0]
    sum_top_n.set(news_num)
    messagebox.showinfo('Message', '爬取即时新闻完成！共{}条有效新闻！'.format(news_num))


def select_news():
    filename = filedialog.askopenfilename(filetypes=[("csv file", "*.csv")])
    if len(filename) == 0:
        return
    news_df = news_pandas.load_news(filename)
    news_pandas.save_news(news_df, os.path.join(news_path, 'news_df.csv'))
    global filter_df
    filter_df = preprocessing.data_filter(news_df)
    news_pandas.save_news(filter_df, os.path.join(temp_news_path, 'filter_news.csv'))
    news_num = filter_df.shape[0]
    sum_top_n.set(news_num)


def data_filter():
    if filter_df.shape[0] == 0:
        messagebox.showinfo('Message', '未选择任何新闻数据！')
        return
    date_f = Entry_Date.get()
    day_f = Entry_Day.get()
    if date_f == '' or day_f == '':
        messagebox.showinfo('Message', '请先填写筛选的日期和天数！')
        return
    global filter_df0
    filter_df0 = preprocessing.get_data(filter_df, last_time=date_f + ' 23:59', delta=int(day_f))
    news_pandas.save_news(filter_df0, os.path.join(temp_news_path, 'filter_news_by_time.csv'))
    news_num = filter_df0.shape[0]
    filter_n.set(news_num)


def show_userdict():
    os.system(editor + ' ' + os.path.join(extra_dict_path, 'self_userdict.txt') + ' &')


def show_stopwords():
    os.system(editor + ' ' + os.path.join(extra_dict_path, 'self_stop_words.txt') + ' &')


def show_disambiguation_dict():
    os.system(editor + ' ' + os.path.join(extra_dict_path, 'self_disambiguation_dict.json') + ' &')


def show_singlewords():
    os.system(editor + ' ' + os.path.join(extra_dict_path, 'self_individual_character_dict.txt') + ' &')


def preprocess():
    if filter_df0.shape[0] == 0:
        messagebox.showinfo('Message', '未选择新闻数据！')
        return
    df = filter_df0.copy()
    df['title_'] = df['title'].map(lambda x: preprocessing.clean_title_blank(x))
    df['content_'] = df['content'].map(lambda x: preprocessing.clean_content(x))
    df['content_'] = df['content_'].map(lambda x: preprocessing.get_num_en_ch(x))
    df['content_cut'] = df['content_'].map(lambda x: preprocessing.pseg_cut(
        x, userdict_path=os.path.join(extra_dict_path, 'self_userdict.txt')))
    df['content_cut'] = df['content_cut'].map(lambda x: preprocessing.get_words_by_flags(
        x, flags=['n.*', 'v.*', 'eng', 't', 's', 'j', 'l', 'i']))
    df['content_cut'] = df['content_cut'].map(lambda x: preprocessing.stop_words_cut(
        x, os.path.join(extra_dict_path, 'self_stop_words.txt')))
    df['content_cut'] = df['content_cut'].map(lambda x: preprocessing.disambiguation_cut(
        x, os.path.join(extra_dict_path, 'self_disambiguation_dict.json')))
    df['content_cut'] = df['content_cut'].map(lambda x: preprocessing.individual_character_cut(
        x, os.path.join(extra_dict_path, 'self_individual_character_dict.txt')))
    df['content_'] = df['content_cut'].map(lambda x: ' '.join(x))
    news_pandas.save_news(df, os.path.join(temp_news_path, 'news_cut.csv'))
    messagebox.showinfo('Message', '数据预处理完成！')


def cluster_content():
    eps_var = Entry_Eps.get()
    min_samples_var = Entry_MinSamples.get()
    if eps_var == '' or min_samples_var == '':
        messagebox.showinfo('Message', '请输全聚类参数！')
        return
    eps_var = float(eps_var)
    min_samples_var = int(min_samples_var)
    try:
        df = news_pandas.load_news(os.path.join(temp_news_path, 'news_cut.csv'))
        df['content_cut'] = df['content_cut'].map(eval)
        df['content_'] = df['content_'].map(str)
    except FileNotFoundError:
        messagebox.showinfo('Message', '请先对新闻内容文本进行预处理！')
        return
    word_library_list = counter.get_word_library(df['content_cut'])
    single_frequency_words_list = counter.get_single_frequency_words(df['content_cut'])
    max_features = len(word_library_list) - len(single_frequency_words_list) // 2
    matrix = modeling.feature_extraction(df['content_'], vectorizer='TfidfVectorizer',
                                         vec_args={'max_df': 0.95, 'min_df': 1, 'max_features': max_features})
    dbscan = modeling.get_cluster(matrix, cluster='DBSCAN',
                                  cluster_args={'eps': eps_var, 'min_samples': min_samples_var, 'metric': 'cosine'})
    labels = modeling.get_labels(dbscan)
    df['label'] = labels
    ranks = modeling.label2rank(labels)
    df['rank'] = ranks
    news_pandas.save_news(df, os.path.join(results_path, 'news_label.csv'))
    df['matrix'] = matrix.toarray().tolist()
    df_non_outliers = df[df['label'] != -1].copy()
    if df_non_outliers.shape[0] == 0:
        messagebox.showinfo('Message', '不能聚类出任何热点，请重新设置聚类参数！')
        return
    data_pca_tsne = modeling.feature_reduction(df_non_outliers['matrix'].tolist(),
                                               pca_n_components=50, tsne_n_components=2)
    df_non_outliers['pca_tsne'] = data_pca_tsne.tolist()
    del df_non_outliers['matrix']
    news_pandas.save_news(df_non_outliers, os.path.join(results_path, 'news_non_outliers.csv'))
    rank_num = counter.get_num_of_value_no_repeat(df_non_outliers['rank'])
    hot_num.set(rank_num)
    messagebox.showinfo('Message', '按照新闻内容聚类完成！')


def show_cluster_result():
    try:
        df_non_outliers = news_pandas.load_news(os.path.join(results_path, 'news_non_outliers.csv'))
        df_non_outliers['pca_tsne'] = df_non_outliers['pca_tsne'].map(eval)
    except FileNotFoundError:
        messagebox.showinfo('Message', '请先对新闻内容文本进行聚类！')
        return
    drawing.draw_clustering_result(df_non_outliers['pca_tsne'], df_non_outliers['label'])


def show_hot_barh():
    try:
        df_non_outliers = news_pandas.load_news(os.path.join(results_path, 'news_non_outliers.csv'))
        df_non_outliers['content_cut'] = df_non_outliers['content_cut'].map(eval)
    except FileNotFoundError:
        messagebox.showinfo('Message', '请先对新闻内容文本进行聚类！')
        return
    rank_num = counter.get_num_of_value_no_repeat(df_non_outliers['rank'])
    value = [df_non_outliers[df_non_outliers['rank'] == i].shape[0] for i in range(1, rank_num + 1)]
    yticks1 = [str(counter.get_most_common_words(df_non_outliers[df_non_outliers['rank'] == i]['content_cut'],
                                                 top_n=10)) + str(i) for i in range(1, rank_num + 1)]
    # yticks2 = [modeling.get_key_sentences('\n'.join(df_non_outliers[df_non_outliers['rank'] == i]['title_']),
    #                                       num=1) for i in range(1, rank_num + 1)]
    drawing.draw_clustering_analysis_barh(rank_num, value, yticks1, title='热点新闻分布饼图')


def show_hot_pie():
    try:
        df_non_outliers = news_pandas.load_news(os.path.join(results_path, 'news_non_outliers.csv'))
        df_non_outliers['content_cut'] = df_non_outliers['content_cut'].map(eval)
    except FileNotFoundError:
        messagebox.showinfo('Message', '请先对新闻内容文本进行聚类！')
        return
    rank_num = counter.get_num_of_value_no_repeat(df_non_outliers['rank'])
    value = [df_non_outliers[df_non_outliers['rank'] == i].shape[0] for i in range(1, rank_num + 1)]
    yticks1 = [counter.get_most_common_words(df_non_outliers[df_non_outliers['rank'] == i]['content_cut'],
                                             top_n=5) for i in range(1, rank_num + 1)]
    # yticks2 = [modeling.get_key_sentences('\n'.join(df_non_outliers[df_non_outliers['rank'] == i]['title_']),
    #                                       num=1) for i in range(1, rank_num + 1)]
    drawing.draw_clustering_analysis_pie(rank_num, value, yticks1)


def show_hot_words_details():
    top_words_list = counter.get_most_common_words(df_rank_i['content_cut'], top_n=5000, min_frequency=1)
    top_words = '\n'.join(top_words_list)
    news_pandas.save_text(top_words, os.path.join(texts_path, 'top_words.txt'))
    os.system(editor + ' ' + os.path.join(texts_path, 'top_words.txt') + ' &')


def show_hot_titles():
    all_title = '\n'.join(df_rank_i['title_'].tolist())
    hot_titles = modeling.get_key_sentences(all_title, num=200)
    news_pandas.save_text(hot_titles, os.path.join(texts_path, 'hot_titles.txt'))
    os.system(editor + ' ' + os.path.join(texts_path, 'hot_titles.txt') + ' &')


def show_word_cluster_result():
    word_df = news_pandas.load_news(os.path.join(results_path, 'word_df.csv'))
    word_df['wordvec'] = word_df['wordvec'].map(eval)
    wordvec_list = word_df['wordvec'].tolist()
    word_label = word_df['word_label'].tolist()
    word_pca_tsne = modeling.feature_reduction(wordvec_list, pca_n_components=2, tsne_n_components=None)
    drawing.draw_clustering_result(word_pca_tsne, word_label)


def show_word_barh():
    word_df = news_pandas.load_news(os.path.join(results_path, 'word_df.csv'))
    word_df['wordvec'] = word_df['wordvec'].map(eval)
    n_clusters = counter.get_num_of_value_no_repeat(word_df['word_label'])
    word_label_value = [word_df[word_df['word_label'] == i].shape[0] for i in range(n_clusters)]
    word_label_yticks = [str(word_df[word_df['word_label'] == i]['word'][:10].tolist()) +
                         str(i + 1) for i in range(n_clusters)]
    drawing.draw_clustering_analysis_barh(n_clusters, word_label_value, word_label_yticks, title='词汇聚类条形图')


def show_word_pie():
    word_df = news_pandas.load_news(os.path.join(results_path, 'word_df.csv'))
    word_df['wordvec'] = word_df['wordvec'].map(eval)
    n_clusters = counter.get_num_of_value_no_repeat(word_df['word_label'])
    word_label_value = [word_df[word_df['word_label'] == i].shape[0] for i in range(n_clusters)]
    word_label_yticks = [word_df[word_df['word_label'] == i]['word'][:5].tolist() for i in range(n_clusters)]
    drawing.draw_clustering_analysis_pie(n_clusters, word_label_value, word_label_yticks)


def show_details():
    top_num = Entry_TopHot.get()
    if top_num == '':
        messagebox.showinfo('Message', '请输入想查看的热点属于第几簇！')
        return
    top_num = int(top_num)
    try:
        df_non_outliers = news_pandas.load_news(os.path.join(results_path, 'news_non_outliers.csv'))
        df_non_outliers['content_cut'] = df_non_outliers['content_cut'].map(eval)
    except FileNotFoundError:
        messagebox.showinfo('Message', '请先对新闻内容文本进行聚类！')
        return
    global df_rank_i
    df_rank_i = df_non_outliers[df_non_outliers['rank'] == top_num]
    all_title = '\n'.join(df_rank_i['title_'].tolist())
    hot_title = modeling.get_key_sentences(all_title, num=1)

    detail_tk = tk.Tk()
    detail_tk.geometry("720x540+323+114")
    detail_tk.title("第{}簇热点详情".format(top_num))

    Label_Title = tk.Label(detail_tk, text='''话题：''')
    Label_Title.place(relx=0.2, rely=0.1, height=26, width=62)
    # Label_HotTitle = tk.Label(detail_tk, text=hot_title, font=('SimHei', 12, 'bold'), fg='red')
    Label_HotTitle = tk.Label(detail_tk, text=hot_title, font=('courier', 12, 'bold'), fg='red')
    Label_HotTitle.place(relx=0.25, rely=0.15)
    Button_HotWords = tk.Button(detail_tk, text='''该处热点相关词汇''', command=show_hot_words_details)
    Button_HotWords.place(relx=0.25, rely=0.25, height=26, width=122)
    Button_HotTitles = tk.Button(detail_tk, text='''该处热点热门话题''', command=show_hot_titles)
    Button_HotTitles.place(relx=0.55, rely=0.25, height=26, width=122)

    Label_L_6 = tk.Label(detail_tk, text='''热点词汇分''')
    Label_L_6.place(relx=0.25, rely=0.4, height=18, width=64)
    n_to_cluster = tk.StringVar()
    Entry_N_Clusters = tk.Entry(detail_tk, textvariable=n_to_cluster)
    # n_to_cluster.set('15')
    Entry_N_Clusters.place(relx=0.35, rely=0.4, height=20, relwidth=0.07)
    Label_R_6 = tk.Label(detail_tk, text='''类聚类''')
    Label_R_6.place(relx=0.43, rely=0.4, height=18, width=40)

    def cluster_word():
        n_clusters = Entry_N_Clusters.get()
        if n_clusters == '':
            messagebox.showinfo('Message', '请输入词汇聚类的类别数！')
            return
        n_clusters = int(n_clusters)
        top_words_list = counter.get_most_common_words(df_rank_i['content_cut'], top_n=5000, min_frequency=1)
        model = news_pandas.load_element(os.path.join(models_path, 'word2vec_model.pkl'))
        word_list, wordvec_list = modeling.get_word_and_wordvec(model, top_words_list)
        kmeans = modeling.get_cluster(wordvec_list, cluster='KMeans', cluster_args={
            'n_clusters': n_clusters, 'random_state': 9})
        word_label = kmeans.labels_
        word_df = pd.DataFrame()
        word_df['word'] = word_list
        word_df['wordvec'] = wordvec_list
        word_df['word_label'] = word_label
        news_pandas.save_news(word_df, os.path.join(results_path, 'word_df.csv'))
        messagebox.showinfo('Message', '词汇聚类完成！')

    Button_WordsCluster = tk.Button(detail_tk, text='''词汇聚类''', command=cluster_word)
    Button_WordsCluster.place(relx=0.55, rely=0.4, height=26, width=74)

    Button_Show_Word_Cluster_Result = tk.Button(detail_tk, text='''查看词汇聚类效果''', command=show_word_cluster_result)
    Button_Show_Word_Cluster_Result.place(relx=0.38, rely=0.51, height=26, width=122)
    Button_Word_Barh = tk.Button(detail_tk, text='''查看词汇聚类条形图''', command=show_word_barh)
    Button_Word_Barh.place(relx=0.38, rely=0.61, height=26, width=134)
    Button_Word_Pie = tk.Button(detail_tk, text='''查看词汇聚类饼图''', command=show_word_pie)
    Button_Word_Pie.place(relx=0.38, rely=0.71, height=26, width=122)

    Label_L_7 = tk.Label(detail_tk, text='''第''')
    Label_L_7.place(relx=0.3, rely=0.84, height=18, width=16)
    cluster_n = tk.StringVar()
    Entry_Cluster_N = tk.Entry(detail_tk, textvariable=cluster_n)
    # cluster_n.set('1')
    Entry_Cluster_N.place(relx=0.34, rely=0.84, height=20, relwidth=0.07)
    Label_R_7 = tk.Label(detail_tk, text='''类词汇''')
    Label_R_7.place(relx=0.42, rely=0.84, height=18, width=40)

    def show_cluster_n_words():
        n = Entry_Cluster_N.get()
        if n == '':
            messagebox.showinfo('Message', '请先输入想要查看的词汇属于第几类！')
            return
        n = int(n)
        try:
            word_df = news_pandas.load_news(os.path.join(results_path, 'word_df.csv'))
        except FileNotFoundError:
            messagebox.showinfo('Message', '请先对新闻内容文本进行聚类！')
            return
        word_df['wordvec'] = word_df['wordvec'].map(eval)
        words_i_df = word_df[word_df['word_label'] == n - 1].copy()
        cluster_i_words = '\n'.join(words_i_df['word'].tolist())
        news_pandas.save_text(cluster_i_words, os.path.join(texts_path, 'cluster_i_words.txt'))
        os.system(editor + ' ' + os.path.join(texts_path, 'cluster_i_words.txt') + ' &')

    Button_Show_Cluster_N_Word = tk.Button(detail_tk, text='''查询''', command=show_cluster_n_words)
    Button_Show_Cluster_N_Word.place(relx=0.55, rely=0.84, height=26, width=50)

    detail_tk.mainloop()


def cut_content():
    try:
        news_df = news_pandas.load_news(os.path.join(news_path, 'news_df.csv'))
    except FileNotFoundError:
        messagebox.showinfo('Message', '没有选择新闻内容文本！')
        return
    document = '\n'.join([str(content) for content in news_df['content']])
    preprocessing.document2txt(document, userdict_path=os.path.join(extra_dict_path, 'self_userdict.txt'),
                               text_path=os.path.join(texts_path, 'document_segment.txt'))
    messagebox.showinfo('Message', '新闻内容文本分词完成！')


def show_content_cut():
    try:
        os.system(editor + ' ' + os.path.join(texts_path, 'document_segment.txt') + ' &')
    except FileNotFoundError:
        messagebox.showinfo('Message', '没有分词后的文件！')
        return


def show_wordlib():
    try:
        document_segment = news_pandas.load_text(os.path.join(texts_path, 'document_segment.txt'))
    except FileNotFoundError:
        messagebox.showinfo('Message', '没有分词后的文件！')
        return
    words = document_segment.split()
    word_library = counter.get_most_common_words(words)
    word_library = [word for word in word_library if re.match(r'^[0-9A-Za-z\u4E00-\u9FFF]+$', word)]
    word_library = '\n'.join(word_library)
    news_pandas.save_text(word_library, os.path.join(texts_path, 'word_library.txt'))
    os.system(editor + ' ' + os.path.join(texts_path, 'word_library.txt') + ' &')


def word2vector():
    try:
        model = modeling.get_word2vec_model(text_path=os.path.join(texts_path, 'document_segment.txt'))
    except FileNotFoundError:
        messagebox.showinfo('Message', '没有分词后的文件！')
        return
    news_pandas.save_element(model, os.path.join(models_path, 'word2vec_model.pkl'))
    messagebox.showinfo('Message', '词向量训练完成！')


def wordsimilar():
    model = news_pandas.load_element(os.path.join(models_path, 'word2vec_model.pkl'))
    word = Entry_Word.get()
    if word == '':
        messagebox.showinfo('Message', '请输入词语！')
        return
    try:
        model.wv.get_vector(word)
    except:
        messagebox.showinfo('Message', '词库中没有此词语！')
        return
    similar_words = model.wv.most_similar(word, topn=100)
    similar_words = str(similar_words)[1:-1]
    similar_words = re.sub(r'\), \(', '),\n(', similar_words)
    news_pandas.save_text(similar_words, os.path.join(texts_path, 'similar_words.txt'))
    os.system(editor + ' ' + os.path.join(texts_path, 'similar_words.txt') + ' &')


Label_Sina = tk.Label(root, text='''新浪''')
Label_Sina.place(relx=0.03, rely=0.05, height=18, width=28)
Label_Sohu = tk.Label(root, text='''搜狐''')
Label_Sohu.place(relx=0.22, rely=0.05, height=18, width=28)
Label_XinhuaNet = tk.Label(root, text='''新华网''')
Label_XinhuaNet.place(relx=0.03, rely=0.15, height=18, width=40)

sina_top_n = tk.StringVar()
Entry_Sina = tk.Entry(root, textvariable=sina_top_n)
sina_top_n.set('6000')
Entry_Sina.place(relx=0.08, rely=0.05, height=20, relwidth=0.07)
sohu_top_n = tk.StringVar()
Entry_Sohu = tk.Entry(root, textvariable=sohu_top_n)
sohu_top_n.set('1000')
Entry_Sohu.place(relx=0.27, rely=0.05, height=20, relwidth=0.07)
xinhuanet_top_n = tk.StringVar()
Entry_XinhuaNet = tk.Entry(root, textvariable=xinhuanet_top_n)
xinhuanet_top_n.set('1000')
Entry_XinhuaNet.place(relx=0.1, rely=0.15, height=20, relwidth=0.07)

Label_T_1 = tk.Label(root, text='''条''')
Label_T_1.place(relx=0.15, rely=0.05, height=18, width=16)
Label_T_2 = tk.Label(root, text='''条''')
Label_T_2.place(relx=0.33, rely=0.05, height=18, width=16)
Label_T_3 = tk.Label(root, text='''条''')
Label_T_3.place(relx=0.17, rely=0.15, height=18, width=16)

Button_Crawler = tk.Button(root, text='''爬取''', command=crawler)
Button_Crawler.place(relx=0.47, rely=0.05, height=26, width=50)
Label_S_1 = tk.Label(root, text='''或''')
Label_S_1.place(relx=0.57, rely=0.08, height=18, width=16)
Button_Select_News = tk.Button(root, text='''选择新闻文件''', command=select_news)
Button_Select_News.place(relx=0.47, rely=0.15, height=26, width=98)

Label_L_1 = tk.Label(root, text='''共''')
Label_L_1.place(relx=0.7, rely=0.1, height=18, width=15)
Label_M_1 = tk.Label(root, textvariable=sum_top_n)
sum_top_n.set('0')
Label_M_1.place(relx=0.73, rely=0.1, height=18, width=35)
Label_R_1 = tk.Label(root, text='''条有效新闻''')
Label_R_1.place(relx=0.8, rely=0.1, height=18, width=64)

Label_L_2 = tk.Label(root, text='''筛选''')
Label_L_2.place(relx=0.03, rely=0.25, height=18, width=28)
date_f = tk.StringVar()
Entry_Date = tk.Entry(root, textvariable=date_f)
date_f.set('2018-05-05')
Entry_Date.place(relx=0.08, rely=0.25, height=19, relwidth=0.24)
Label_Date = tk.Label(root, text='''日期前''')
Label_Date.place(relx=0.33, rely=0.25, height=18, width=40)
day_f = tk.StringVar()
Entry_Day = tk.Entry(root, textvariable=day_f)
day_f.set('5')
Entry_Day.place(relx=0.4, rely=0.25, height=20, relwidth=0.07)
Label_R_2 = tk.Label(root, text='''天的新闻''')
Label_R_2.place(relx=0.47, rely=0.25, height=18, width=64)

Button_Filter = tk.Button(root, text='''筛选''', command=data_filter)
Button_Filter.place(relx=0.63, rely=0.25, height=26, width=50)
Label_L_3 = tk.Label(root, text='''筛选出''')
Label_L_3.place(relx=0.73, rely=0.25, height=18, width=40)
Label_M_3 = tk.Label(root, textvariable=filter_n)
filter_n.set('0')
Label_M_3.place(relx=0.8, rely=0.25, height=18, width=32)
Label_R_3 = tk.Label(root, text='''条新闻''')
Label_R_3.place(relx=0.87, rely=0.25, height=18, width=40)

Button_UserDict = tk.Button(root, text='''用户词词典''', command=show_userdict)
Button_UserDict.place(relx=0.05, rely=0.35, height=26, width=86)
Button_StopWords = tk.Button(root, text='''停用词词典''', command=show_stopwords)
Button_StopWords.place(relx=0.22, rely=0.35, height=26, width=86)
Button_Disambiguation = tk.Button(root, text='''消歧词典''', command=show_disambiguation_dict)
Button_Disambiguation.place(relx=0.38, rely=0.35, height=26, width=74)
Button_Single = tk.Button(root, text='''保留单字''', command=show_singlewords)
Button_Single.place(relx=0.53, rely=0.35, height=26, width=74)

Button_Preprocess = tk.Button(root, text='''数据预处理''', command=preprocess)
Button_Preprocess.place(relx=0.73, rely=0.35, height=26, width=86)

Label_Eps = tk.Label(root, text='''聚类参数：  扫描半径：''')
Label_Eps.place(relx=0.05, rely=0.45, height=18, width=136)
eps_var = tk.StringVar()
Entry_Eps = tk.Entry(root, textvariable=eps_var)
eps_var.set('0.43')
Entry_Eps.place(relx=0.24, rely=0.45, height=20, relwidth=0.08)

Label_MinSamples = tk.Label(root, text='''最小包含点数：''')
Label_MinSamples.place(relx=0.36, rely=0.45, height=18, width=88)
min_samples_var = tk.StringVar()
Entry_MinSamples = tk.Entry(root, textvariable=min_samples_var)
min_samples_var.set('10')
Entry_MinSamples.place(relx=0.49, rely=0.45, height=20, relwidth=0.08)

Button_Cluster = tk.Button(root, text='''对新闻内容文本进行聚类''', command=cluster_content)
Button_Cluster.place(relx=0.63, rely=0.45, height=26, width=158)

Label_L_4 = tk.Label(root, text='''共获得''')
Label_L_4.place(relx=0.67, rely=0.55, height=18, width=40)
Label_M_4 = tk.Label(root, textvariable=hot_num)
hot_num.set('0')
Label_M_4.place(relx=0.75, rely=0.55, height=18, width=18)
Label_R_4 = tk.Label(root, text='''处热点''')
Label_R_4.place(relx=0.8, rely=0.55, height=18, width=40)

Button_Show1 = tk.Button(root, text='''查看聚类效果图''', command=show_cluster_result)
Button_Show1.place(relx=0.05, rely=0.55, height=26, width=110)
Button_Show2 = tk.Button(root, text='''查看热点条形图''', command=show_hot_barh)
Button_Show2.place(relx=0.27, rely=0.55, height=26, width=110)
Button_Show3 = tk.Button(root, text='''查看热点饼图''', command=show_hot_pie)
Button_Show3.place(relx=0.47, rely=0.55, height=26, width=98)

Label_L_5 = tk.Label(root, text='''第''')
Label_L_5.place(relx=0.42, rely=0.65, height=18, width=16)
top_num = tk.StringVar()
Entry_TopHot = tk.Entry(root, textvariable=top_num)
top_num.set('1')
Entry_TopHot.place(relx=0.47, rely=0.65, height=20, relwidth=0.08)
Label_R_5 = tk.Label(root, text='''簇热点''')
Label_R_5.place(relx=0.57, rely=0.65, height=18, width=40)
Button_Show4 = tk.Button(root, text='''点击查看详情''', command=show_details)
Button_Show4.place(relx=0.67, rely=0.65, height=26, width=98)

Label_S_2 = tk.Label(root, text='''-''' * 200)
Label_S_2.place(relx=0.0, rely=0.72)

Button_CutContent = tk.Button(root, text='''对新闻内容做分词处理''', command=cut_content)
Button_CutContent.place(relx=0.05, rely=0.8, height=26, width=146)
Button_ShowCut = tk.Button(root, text='''打开分词后的文件''', command=show_content_cut)
Button_ShowCut.place(relx=0.31, rely=0.8, height=26, width=122)
Button_WordLib = tk.Button(root, text='''生成总词库''', command=show_wordlib)
Button_WordLib.place(relx=0.54, rely=0.8, height=26, width=86)
Button_Word2Vec = tk.Button(root, text='''训练词向量''', command=word2vector)
Button_Word2Vec.place(relx=0.71, rely=0.8, height=26, width=86)

word = tk.StringVar()
Entry_Word = tk.Entry(root, textvariable=word)
word.set('中国')
Entry_Word.place(relx=0.05, rely=0.9, height=20, relwidth=0.5)
Button_WordSim = tk.Button(root, text='''相近词查询''', command=wordsimilar)
Button_WordSim.place(relx=0.6, rely=0.9, height=26, width=86)

root.mainloop()
