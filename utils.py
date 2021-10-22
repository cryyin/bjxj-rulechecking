# Author: shen chunyuan, Datetime: 2021-10-22
# provide some utility functions
# -*- coding: utf-8 -*-

# 正则包
import re


# 统一单位进行大小比较
def greater_uniform(a, b):
    while a > 1:
        a = a / 10

    while b > 1:
        b = b / 10

    return a > b


def smaller_uniform(a, b):
    while a > 1:
        a = a / 10

    while b > 1:
        b = b / 10

    return a < b


def equal_uniform(a, b):
    while a > 1:
        a = a / 10

    while b > 1:
        b = b / 10

    return a == b


def minus_uniform(a, b):
    ratio_a = 1
    while a > 1:
        a = a / 10
        ratio_a *= 10

    ratio_b = 1
    while b > 1:
        b = b / 10
        ratio_b *= 10

    return (a - b) * min(ratio_a, ratio_b)


# to log all errors
count_error = 1  # global error id


def log_error(error_, errors, flag_print=True):
    global count_error
    error_['id'] = count_error
    if 'errorMsg' not in error_:
        error_['errorMsg'] = error_['errorTitle']
    errors.append(error_)

    if flag_print:
        print('{', end=' ')
        print('id: ', error_['id'], end='; ', sep='')
        for key, value in error_.items():
            if key != 'id' and value:
                print(key, ': ', value, end='; ', sep='')

        print('}')

    count_error += 1

    return errors


# 迭代地拼接表格里的data, 有的文本是分行的， 例如 0.02mm/0.5m  写为了 0.02mm\n0.5m
def recursive_add(table):
    data = ''

    if 'category' in table and table['category'] == 'TEXT':
        data = ''.join(table['data'])
        return data

    if isinstance(table, dict):
        for key, values in table.items():
            if values:  # not None type
                for value in values:
                    data += recursive_add(value) + ' '
    elif isinstance(table, list):
        for row in table:
            data += recursive_add(row) + ' '

    return data


# 判断满不满足要求
def check_requirement(text):
    # text: string
    if '不满足' in text:
        return 0

    if '满足' in text:
        return 1

    # 没有 满足要求的描述
    return 2


# 对某个条目进行检测
def check_item(data, item_name, sec_name):
    # data: 计算书数据字典
    # item_name: 要检测的条目名称
    error_ = {}
    if item_name in data:
        if isinstance(data[item_name], dict):
            for key, value in data[item_name].items():
                check_res = check_requirement(value)
                if check_res == 0:
                    error_['errorCode'] = 1001
                    error_['errorTitle'] = '计算书中信息错误'
                    error_['errorMsg'] = "{:s} {:s} {:s} 验算结果不满足要求!".format(sec_name, item_name, key)
                elif check_res == 2:
                    error_['errorCode'] = 1002
                    error_['errorTitle'] = '计算书中缺少必要信息'
                    error_['errorMsg'] = "{:s} {:s} {:s} 验算结果缺少满足要求的描述".format(sec_name, item_name, key)
        elif isinstance(data[item_name], str):
            check_res = check_requirement(data[item_name])
            if check_res == 0:
                error_['errorCode'] = 1001
                error_['errorTitle'] = '计算书中信息错误'
                error_['errorMsg'] = "{:s} {:s} 验算结果不满足要求!".format(sec_name, item_name)
            elif check_res == 2:
                error_['errorCode'] = 1002
                error_['errorTitle'] = '计算书中缺少必要信息'
                error_['errorMsg'] = "{:s} {:s} 验算结果缺少满足要求的描述".format(sec_name, item_name)

    return error_


# 检验句子中是否至少包含一个词
def check_words(words, sent):
    # words: list of words
    # sent: string
    for word in words:
        if word in sent:
            return True

    return False


# 获取项目目录字典
def obtain_list_of_content(data_CAD):
    global count_error
    if 'table' in data_CAD and data_CAD['table']:
        tables_all = data_CAD['table']
    else:
        return None

    list_of_content = {}  #

    if 'directory' in tables_all:
        tableGroup = tables_all['directory']['tableGroup']
    else:
        return None

    for table in tableGroup:
        for row in table['table']:
            if row['row'][1]['category'] == 'TEXT' and re.search(r'\d+', ''.join(row['row'][1]['data']).strip()):
                # 文档的编号
                id = ''.join(row['row'][1]['data']).strip()
                name = ''.join(row['row'][2]['data']).strip()  # 获取文档名字
                list_of_content[name] = id

    return list_of_content


def is_number(s):
    try:  # 如果能运行float(s)语句，返回True（字符串s是浮点数）
        float(s)
        return True
    except ValueError:  # ValueError为Python的一种标准异常，表示"传入无效的参数"
        pass  # 如果引发了ValueError这种异常，不做任何事情（pass：不做任何事情，一般用做占位语句）
    try:
        import unicodedata  # 处理ASCii码的包
        unicodedata.numeric(s)  # 把一个表示数字的字符串转换为浮点数返回的函数
        return True
    except (TypeError, ValueError):
        pass
    return False


