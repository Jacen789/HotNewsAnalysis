# -*- coding: utf-8 -*-

import os
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

file_dir_path = os.path.dirname(os.path.realpath(__file__))  # 当前文件所在目录路径
images_path = os.path.join(os.path.dirname(file_dir_path), 'data', 'images')  # 图片存储的目录路径


def draw_clustering_result(data_pca_tsne, label):
    """绘制聚类效果图"""
    plt.figure()
    x = [i[0] for i in data_pca_tsne]
    y = [i[1] for i in data_pca_tsne]
    plt.scatter(x, y, c=label)
    plt.savefig(os.path.join(images_path, '1.jpg'))
    plt.show()


def draw_clustering_analysis_barh(rank_num, value, yticks, title):
    """绘制聚类分析结果条形图"""
    plt.figure(figsize=(13, 6), dpi=100)
    plt.subplot(122)
    ax = plt.gca()
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.invert_yaxis()
    plt.barh(range(1, rank_num + 1), value, align='center', linewidth=0)
    plt.yticks(range(1, rank_num + 1), yticks)
    for a, b in zip(value, range(1, rank_num + 1)):
        plt.text(a + 1, b, '%.0f' % a, ha='left', va='center')
    plt.title(title)
    plt.savefig(os.path.join(images_path, '2.jpg'))
    plt.show()


def draw_clustering_analysis_pie(rank_num, value, yticks):
    """绘制聚类分析结果饼图"""
    plt.figure(figsize=(13, 6), dpi=100)
    plt.subplot(132)
    plt.pie(value, explode=[0.2] * rank_num, labels=yticks, autopct='%1.2f%%', pctdistance=0.7)
    plt.savefig(os.path.join(images_path, '3.jpg'))
    plt.show()
