# -*- coding: utf-8 -*-

from collections import Counter


def flat(l):
    """平展多维列表"""
    for k in l:
        if not isinstance(k, (list, tuple)):
            yield k
        else:
            yield from flat(k)


def get_word_library(list1):
    """
    获得词库
    :param list1: 一维或多维词列表
    :return: list，所有词去重之后的列表
    """
    list2 = flat(list1)
    list3 = list(set(list2))
    return list3


def get_single_frequency_words(list1):
    """
    获得单频词列表
    :param list1: 一维或多维词列表
    :return: list，所有只出现一次的词组成的列表
    """
    list2 = flat(list1)
    cnt = Counter(list2)
    list3 = [i for i in cnt if cnt[i] == 1]
    return list3


def get_most_common_words(list1, top_n=None, min_frequency=1):
    """
    获取最常见的词组成的列表
    :param list1: 一维或多维词列表
    :param top_n: 指定最常见的前n个词，默认为None
    :param min_frequency: 指定最小频数，默认为1
    :return: list，最常见的前n个词组成的列表
    """
    list2 = flat(list1)
    cnt = Counter(list2)
    list3 = [i[0] for i in cnt.most_common(top_n) if cnt[i[0]] >= min_frequency]
    return list3


def get_num_of_value_no_repeat(list1):
    """
    获取列表中不重复的值的个数
    :param list1: 列表
    :return: int，列表中不重复的值的个数
    """
    num = len(set(list1))
    return num
