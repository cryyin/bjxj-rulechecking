# Author: shen chunyuan, Datetime: 2021-10-22
# Regulation Checking
import re

import pandas
import pandas as pd

from read_items import *
from utils import *
import numpy as np
#import chardet
#import sys

# 中文数字与阿拉伯数字的映射
chinese2arabic = {'一': '1', '首': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6', '七': '7', '八': '8', '九': '9',
                  '十': '10'}
arabic2chinese = dict((value, key) for key, value in chinese2arabic.items())
arabic2chinese['1'] = '一'


def strQ2B(ustring):
    """全角转半角"""
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 12288:  # 全角空格直接转换
            inside_code = 32
        elif (inside_code >= 65281 and inside_code <= 65374):  # 全角字符（除空格）根据关系转化
            inside_code -= 65248

        rstring += chr(inside_code)
    return rstring


def strB2Q(ustring):
    """半角转全角"""
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 32:  # 半角空格直接转化
            inside_code = 12288
        elif inside_code >= 32 and inside_code <= 126:  # 半角字符（除空格）根据关系转化
            inside_code += 65248

        rstring += chr(inside_code)
    return rstring


# 3 平面图审核
def rule_3_3(data_CAD, data_calc):
    print("3.3 支护形式审查开始...")
    errors = []

    if 'enclosureStructureLayoutPlan' in data_CAD and data_CAD['enclosureStructureLayoutPlan']:
        data_plan = data_CAD['enclosureStructureLayoutPlan']
    else:
        error_ = {'errorCode': 405, 'errorTitle': '缺少平面图(enclosureStructureLayoutPlan)提取结果', 'path': []}
        log_error(error_, errors)

        return errors

    # 获取计算书中的支护间距
    max_distance = {}
    for sec_name, sec_value in data_calc['支护间距'].items():  # dictionary {"3-3剖面":{"1": “6.000”}}
        if re.search(r'\d-\d', sec_name):
            name = re.search(r'\d-\d', sec_name).group(0)
        else:
            if re.search(r'剖面', sec_name):
                error_ = {'file': '计算书', 'errorCode': 1001, 'errorTitle': '计算书中信息错误',
                          'errorMsg': '计算书中的剖面名称为：{:s}，无数字编号'.format(sec_name), 'path': []}
                log_error(error_, errors)
            else:
                error_ = {'file': '计算书', 'errorCode': 1001, 'errorTitle': '计算书中信息错误',
                          'errorMsg': '计算书中未找到剖面名称', 'path': []}
                log_error(error_, errors)

            name = sec_name

        max_distance[name] = sec_value

    for sec_name, distances in max_distance.items():
        for strut_no, distance in distances.items():
            max_distance[sec_name][strut_no] = float(distance) * 1000  # 单位是 m，换算成 mm

    for filename, content in data_plan.items():
        # 桩径判断，钻孔灌注桩桩径宜取 600mm～1200mm
        diameter_dict = {}  # used to remove repitative errors
        distance_dict = {}  # to remove duplicate errors
        if 'pile' in content:
            prev_diameter = 0.0


            #钻孔灌注桩标注检查
            #print(content['pile'])
            nameHadNoStandard_set=set()#存没有有标准，即没有直径和距离的钻孔的名字
            for pile in content['pile']:
                #print(pile)
                nameHadNoStandard_set.add(pile['name'])
            #print('全部钻孔名称：')
            #print(nameHadNoStandard_set)
            for pile in content['pile']:
                if pile.get('diameter') and pile.get('distance'):
                    nameHadNoStandard_set.discard(pile['name'])
                    #print(pile['name']+' got a Standard')
            #print('缺少标注钻孔名称：')
            #print(nameHadNoStandard_set)
            error_ = {'file': filename, 'errorCode': 417, 'errorTitle': '图纸中缺少必要信息(钻孔灌注桩标注)',
                                        'errorMsg': '桩{:s}缺少标注信息，请检查直径和间距信息'.format(','.join(nameHadNoStandard_set)),
                                        'path': []}
            log_error(error_, errors)





            for pile in content['pile']:
                if 'diameter' in pile and pile['diameter']:
                    prev_diameter = pile['diameter'][len(pile['diameter']) - 1]
                    for diameter in pile['diameter']:
                        if diameter not in diameter_dict:
                            if diameter < 600 or diameter > 1200:
                                error_ = {'file': filename, 'errorCode': 2001, 'errorTitle': '桩径不满足要求',
                                          'errorMsg': '桩{:s}的桩径为{:.0f}，不满足 600mm~1200mm 的要求'.format(pile['name'],
                                                                                                    diameter),
                                          'path': pile['bounding']}
                                log_error(error_, errors)
                            diameter_dict[diameter] = 1

            # 桩间距判断，桩间净距宜为 150mm～1000mm
            # 保留最近的桩径，以防当前的柱没有提取到桩径
            if prev_diameter == 0:  # 没有提取到桩径信息
                error_ = {'file': filename, 'errorCode': 416, 'errorTitle': '图纸中缺少必要信息(桩径)', 'path': []}
                log_error(error_, errors)
            else:  # 有桩径信息，才去判断桩间净距
                for pile in content['pile']:
                    if 'diameter' in pile and pile['diameter']:
                        diameter = pile['diameter'][len(pile['diameter']) - 1]
                        prev_diameter = diameter
                    else:
                        diameter = prev_diameter

                    if 'distance' in pile and pile['distance']:
                        for distance in pile['distance']:
                            if distance not in distance_dict:
                                distance_clean = distance - diameter
                                if distance_clean < 150 or distance_clean > 1000:
                                    error_ = {'file': filename, 'errorCode': 2002, 'errorTitle': '桩间净距不满足要求',
                                              'errorMsg': "桩{:s}的桩间净距为{:.0f}, 不满足150mm~1000mm的要求".format(pile['name'],
                                                                                                         distance_clean),
                                              'path': pile['bounding']}
                                    log_error(error_, errors)

                                distance_dict[distance] = 1

        # 支护间距审核，跟计算书里的支锚水平间距进行比对，不能大于该值
        steel_no = []
        if 'title' in content and content['title']:  # 判断是第几道钢支撑
            for number in chinese2arabic:
                if number in content['title']:
                    steel_no.append(chinese2arabic[number])

        if 'range' in content:
            for strut in content['range']:
                if 'section' in strut:
                    if re.search(r'\d-\d', strut['section']) is not None:
                        sec_id = re.search(r'\d-\d', strut['section']).group(0)
                    else:
                        continue
                    if sec_id in max_distance:
                        cur_max_dist = max_distance[sec_id][steel_no[0]]
                        if len(strut['range']) > 0:
                            prev_distance = 0
                            for strut_id, distance in enumerate(strut['range'][0]['distance']):
                                if strut_id == 0:
                                    prev_distance = distance['value']
                                if (prev_distance + distance['value']) / 2 > cur_max_dist and distance[
                                    'value'] > cur_max_dist:
                                    error_ = {'file': filename, 'errorCode': 2003, 'errorTitle': '支护间距不满足要求',
                                              'errorMsg': "第{:s}道钢支撑 {:s}剖面 第{:d}个支撑的水平间距{:.2f} 超过了最大值{:.2f}的要求".format(
                                                  arabic2chinese[steel_no[0]], sec_id, strut_id + 1, distance['value'],
                                                  cur_max_dist), 'path': distance['bounding']}
                                    log_error(error_, errors)

                                prev_distance = distance['value']

    print("3.3 支护形式审查完毕。\n")
    return errors


# 4 剖面图审核
def rule_4_1(data_CAD):
    print("4.1 地下水位检查开始...")
    errors = []

    if 'designDescription' in data_CAD and data_CAD['designDescription']:
        data_general = data_CAD['designDescription']
    else:
        error_ = {'errorCode': 406, 'errorTitle': '缺少总说明(designDescription)提取结果', 'path': []}
        log_error(error_, errors)
        return errors

    general_info = ''

    for filename, content in data_general.items():
        general_info += "\n".join(content['content'])

    if 'enclosureStructureCrossSection' in data_CAD and data_CAD['enclosureStructureCrossSection']:
        data_section = data_CAD['enclosureStructureCrossSection']
    else:
        error_ = {'errorCode': 407, 'errorTitle': '缺少剖面图(enclosureStructureCrossSection)提取结果', 'path': []}
        log_error(error_, errors)
        return errors

    keywords = ['施工防排水', '施工降排水']

    for filename, section in data_section.items():
        for idx, content in enumerate(section['section']):
            if 'ground_water_level' in content and content['ground_water_level']:
                # obtain the highest level of round water
                ground_water_level = -10000

                for level_str in content['ground_water_level']:  # 有可能有多个提取的文字
                    for level in re.findall(r"\d+.\d+|\d+", level_str):  # 每个文字里有可能有多个数值
                        if ground_water_level < float(level):
                            ground_water_level = float(level)

                if 'bottom_level' in content and content['bottom_level']:
                    bottom_level = content['bottom_level']
                    # 有可能存在单位不统一
                    if not greater_uniform(bottom_level, ground_water_level):
                        # 去总说明中查看有没有止水或降排水措施
                        difference = minus_uniform(ground_water_level, bottom_level)
                        if not check_words(keywords, general_info):
                            error_ = {'file': filename, 'errorCode': 2004, 'errorTitle': '设计总说明缺少必要描述',
                                      'errorMsg': "第{:d}剖面的基坑底在含水层{:.2f}米以下，总说明中缺少止水或降水措施".format(idx + 1, difference),
                                      'path': content['bounding']}
                            log_error(error_, errors)

    print("4.1 地下水位检查完毕。\n")
    return errors


# 基坑嵌固深度审核
def rule_4_3(data_CAD, data_calc):
    print("4.3 基坑嵌固深度检查开始...")
    errors = []

    if 'enclosureStructureCrossSection' in data_CAD and data_CAD['enclosureStructureCrossSection']:
        data_section = data_CAD['enclosureStructureCrossSection']
    else:
        error_ = {'errorCode': 407, 'errorTitle': '缺少剖面图(enclosureStructureCrossSection)提取结果', 'path': []}
        log_error(error_, errors)
        return errors

    embed_depth_CAD = {}  # CAD图纸中的嵌固深度
    bounding = {}
    for filename, section in data_section.items():
        for idx, content in enumerate(section['section']):
            if content['title'] != None:
                if 'embedment_depth' in content and content['embedment_depth']:
                    sec_name = re.search(r'\d-\d', content['title']).group(0)
                    embed_depth_CAD[sec_name] = content['embedment_depth']
                    bounding[sec_name] = content['bounding']
                else:
                    error_ = {'file': filename, 'errorCode': 418, 'errorTitle': 'CAD图纸中缺少嵌固深度',
                              'errorMsg': "图纸{:s} 中缺少{:s} 的嵌固深度".format(filename, content['title']),
                              'path': content['bounding']}
                    log_error(error_, errors)



    embed_depth_calc = {}  # 计算书中的嵌固深度
    if '嵌固深度' in data_calc and data_calc['嵌固深度']:
        for title, value in data_calc['嵌固深度'].items():
            if re.search(r'\d-\d', title):
                sec_name = re.search(r'\d-\d', title).group(0)
            else:
                sec_name = title

            embed_depth_calc[sec_name] = float(value)
    else:
        for key in bounding:
            error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整', 'errorMsg': "请核对计算书中嵌固深度信息",
                      'path': bounding[key]}
            log_error(error_, errors)


        return errors

    # 需要考虑单位换算
    for key, value_CAD in embed_depth_CAD.items():
        if key in embed_depth_calc:
            value_calc = embed_depth_calc[key]
            if not equal_uniform(value_CAD, value_calc):
                error_ = {'file': '计算书', 'errorCode': 3002, 'errorTitle': '图纸与计算书信息不符',
                          'errorMsg': "剖面{:s} 的嵌固深度不符，图纸中为 {:.2f}, 计算书中为 {:.2f}".format(key, value_CAD, value_calc),
                          'path': bounding[key]}
                log_error(error_, errors)

    print("4.3 基坑嵌固深度检查完毕。\n")
    return errors


# 钢支撑轴力值审核
def rule_4_4(data_CAD, data_calc, list_of_content=None):
    errors = []
    print("4.4 钢支撑轴力值检查开始...")

    # 获取CAD里的钢支撑轴力值表
    zhouli_CAD = {}
    boundings = []
    file_list = []
    # 获取表格
    if 'table' in data_CAD and data_CAD['table']:
        tables_all = data_CAD['table']
    else:
        error_ = {'errorCode': 413, 'errorTitle': '缺少钢支撑轴力值表格(enclosureStructureCrossSection)提取结果', 'path': []}
        log_error(error_, errors)
        return errors

    flag = False
    for key, value in list_of_content.items():
        if '监控量测' not in key and re.search(r'[^纵]剖面图', key):
            strut_table = {}
            row_title = []
            col_title = []
            if re.search(r'\d-\d', key):
                sec_name = ' '.join(re.findall(r'\d-\d', key))
            else:
                sec_name = key
            if value in tables_all:
                flag = True
                tableGroup = tables_all[value]['tableGroup']
                for id_table, table in enumerate(tableGroup):
                    # 获取表格的第一行所有单元格的文字
                    row0_text = ''
                    for row0_col in table['table'][0]['row']:
                        if row0_col['category'] == 'TEXT':
                            if row0_col['data']:
                                row0_text += row0_col['data'][0] + ' '
                            else:
                                row0_text += ' '
                    if '支撑' in row0_text and '轴力' in row0_text:  # 判断是钢支撑轴力表
                        strut_no_col = 0  # 判断哪一列为支撑道数
                        for id_row, row in enumerate(table['table']):
                            strut_value = {}
                            for id_col, col in enumerate(row['row']):
                                if id_row == 0:
                                    if col['category'] == 'TEXT':
                                        col_title.append(''.join(col['data']))
                                        if re.search(r'支撑(道数)?', ''.join(col['data'])):
                                            strut_no_col = id_col
                        if strut_no_col == 0:
                            table_part = table['table'][1:]
                        else:
                            table_part = table['table'][1]['row'][1]['table']
                            for zhicheng_id, zhouli_value in enumerate(table['table'][1]['row'][1]['table']):
                                table_part[zhicheng_id]['row'].extend(
                                    table['table'][1]['row'][2]['table'][zhicheng_id]['row'])
                                table_part[zhicheng_id]['row'].extend(
                                    table['table'][1]['row'][3]['table'][zhicheng_id]['row'])

                        for id_row, row in enumerate(table_part):
                            strut_value = {}
                            for id_col, col in enumerate(row['row']):
                                if id_col == 0:
                                    strut_key_res = re.search(r'第(\w)道', ''.join(col['data']))
                                    if strut_key_res:
                                        strut_key = chinese2arabic[strut_key_res.group(1)]
                                        row_title.append(strut_key)
                                else:
                                    strut_value[col_title[id_col + strut_no_col]] = ''.join(col['data'])
                            if strut_value:
                                strut_table[strut_key] = strut_value
                        # 加 *** 为了处理一个CAD文件中有两个轴力表
                        zhouli_CAD[sec_name + "@" + str(id_table)] = [strut_table, table['bounding'], value]

    if not flag:
        error_ = {'errorCode': 413, 'errorTitle': '缺少钢支撑轴力值表格(enclosureStructureCrossSection)提取结果', 'path': []}
        log_error(error_, errors)
        return errors

    if '钢支撑轴力' in data_calc and data_calc['钢支撑轴力']:
        zhouli_calc = data_calc['钢支撑轴力']
    else:
        error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整', 'errorMsg': '请核对计算书中钢支撑轴力', 'path': []}
        log_error(error_, errors)
        return errors
    # 匹配图纸和计算书中的轴力值表
    for sec_no, sec_table in zhouli_CAD.items():
        sec_list = sec_no.split('@')[0].split()
        for sec_id in sec_list:
            for sec_no_calc, sec_table_calc in zhouli_calc.items():
                if sec_id in sec_no_calc:
                    for line_no, value in sec_table_calc.items():
                        value_calc = re.search(r'\d+.\d+|\d+', str(value)).group(0)
                        all_values_CAD = ''
                        if re.search(r'^\d+$', ''.join(line_no)) is None:
                            temp_line_no = re.search(r'第(.)道', ''.join(line_no))
                            line_no = chinese2arabic[temp_line_no.group(1)]
                        for col_name, col_value in sec_table[0][line_no].items():
                            all_values_CAD += ' '.join(re.findall(r'\d+.\d+|\d+', col_value)) + ' '
                        if value_calc not in all_values_CAD:  # 判断图纸中的轴力与计算书中的轴力相不相等
                            error_ = {'file': sec_table[2],
                                      'errorCode': 3002,
                                      'errorTitle': '图纸与计算书信息不符',
                                      'errorMsg': "剖面{:s} {:s} 钢支撑轴力值与计算书不符，图纸中为 {:s}, 计算书中为 {:s}".format(sec_id,
                                                                                                          line_no,
                                                                                                          all_values_CAD,
                                                                                                          value_calc),
                                      'path': sec_table[1]}
                            # error_['file']='计算书'
                            log_error(error_, errors)

    print("4.4 钢支撑轴力值检查完毕。\n")
    return errors


def rule_4_6(data_CAD, data_calc):
    errors = []

    print("4.6 挡墙检查开始...")

    if 'enclosureStructureCrossSection' in data_CAD and data_CAD['enclosureStructureCrossSection']:
        for filename, sections in data_CAD['enclosureStructureCrossSection'].items():
            for section in sections['section']:
                if 'wall_text' in section and section['wall_text']:
                    wall_texts = ' '.join(section['wall_text'])
                    if '钢筋混凝土' in wall_texts:  # 如果是钢筋混凝土挡墙，确认一下计算书中有没有 挡土墙验算
                        if '挡土墙' not in data_calc or not data_calc['挡土墙']:
                            error_ = {'file': filename, 'errorCode': 3001, 'errorTitle': '补充必要的计算内容',
                                      'errorMsg': "图纸中有钢筋混凝土挡墙，但计算书中缺少验算", 'path': section['bounding']}
                            log_error(error_, errors)
                    elif '砖砌挡墙' in wall_texts:
                        if '挡土墙' not in data_calc or not data_calc['挡土墙']:
                            error_ = {'file': filename, 'errorCode': 3001, 'errorTitle': '补充必要的计算内容',
                                      'errorMsg': "图纸中有砖砌挡墙，但计算书中缺少合规性检查", 'path': section['bounding']}
                            log_error(error_, errors)

    print("4.6 挡墙检查完毕。\n")
    return errors


######################
# 6 内支撑详图

def rule_6(data_CAD):
    errors = []

    print("6 内支撑详图检查开始...")

    flag_shear = False  # 肋板、抗剪措施
    flag_anti_fall = False  # 防脱落措施
    flag_flange = False  # 法兰盘
    if 'enclosureStructureDetailDrawing' in data_CAD and data_CAD['enclosureStructureDetailDrawing']:
        data_internal = data_CAD['enclosureStructureDetailDrawing']
        for filename, content in data_internal.items():
            if 'shear_measures' in content and content['shear_measures'] == 1:
                flag_shear = True
            if 'anti_falling_measures' in content and content['anti_falling_measures'] == 1:
                flag_anti_fall = True
            if 'flange_plate' in content and content['flange_plate'] > 0:
                flag_flange = True
        if not flag_shear:
            for file, content in data_internal.items():
                error_ = {'file': file, 'errorCode': 2009, 'errorTitle': '请核对图纸中肋板、抗剪措施', 'path': []}
                log_error(error_, errors)

        if not flag_anti_fall:
            for file, content in data_internal.items():
                error_ = {'file': file, 'errorCode': 2010, 'errorTitle': '请核对钢支撑防脱落措施', 'path': []} #图纸中缺少必要信息(防脱落措施)
                log_error(error_, errors)

        if not flag_flange:
            for file, content in data_internal.items():
                error_ = {'file': file, 'errorCode': 2011, 'errorTitle': '请核对图纸中法兰盘螺栓连接方式', 'path': []}
                log_error(error_, errors)
    else:
        error_ = {'file': '', 'errorCode': 409, 'errorTitle': '缺少内支撑详图(enclosureStructureDetailDrawing)提取结果',
                  'path': []}
        log_error(error_, errors)

    print("6 内支撑详图检查完毕。\n")
    return errors


######################
# 7 施工步序

# 7.1 与计算工况是否一致建议人工复核

def rule_7_1(data_CAD):
    errors = []

    print("7 施工步序图检查开始...")

    if 'constructionSteps' in data_CAD and data_CAD['constructionSteps']:
        data_internal = data_CAD['constructionSteps']
        for filename, contents in data_internal.items():
            for content in contents['content']:
                if re.search(r"第.{1,2}步(:|：)", content):
                    step = re.search(r"第.{1,2}步(:|：)", content).group(0)
                    # 检测架设钢支撑间距
                    if re.search(r"(架设|施作).[^拆除]*?支撑", content):
                        distances = []
                        temps = re.findall(r"\d+.\d+(?:mm|m)|\d+(?:mm|m)", content)
                        for temp in temps:
                            distances.append(float(re.search(r"\d+.\d+|\d+", temp).group(0)))
                            BasicUnit=re.search(r"mm|m", temp).group(0)
                        for distance in distances:
                            if BasicUnit == 'mm' and distance != 500.0:
                                error_ = {'file': filename, 'errorCode': 2005, 'errorTitle': '图纸与规范不符',
                                          'errorMsg': step + "架设间距不满足 0.5m 要求", 'path': []}
                                log_error(error_, errors)
                            elif BasicUnit == 'm' and distance != 0.5:
                                error_ = {'file': filename, 'errorCode': 2005, 'errorTitle': '图纸与规范不符',
                                          'errorMsg': step + "架设间距不满足 0.5m 要求", 'path': []}
                                log_error(error_, errors)

                    # 检测支撑强度
                    if re.search(r"设计强度", content):
                        nums = []
                        temps = re.findall(r"\d+.\d+％|\d+％", content)
                        for temp in temps:
                            nums.append(float(re.search(r"\d+.\d+|\d+", temp).group(0)))
                        for num in nums:
                            if num <= 80:
                                error_ = {'file': filename, 'errorCode': 2005, 'errorTitle': '图纸与规范不符',
                                          'errorMsg': step + "拆除时设计强度未达到 80% 要求", 'path': []}
                                log_error(error_, errors)

    else:
        error_ = {'file': '', 'errorCode': 410, 'errorTitle': '缺少施工步序图(constructionSteps)提取结果', 'path': []}
        log_error(error_, errors)

    print("7 施工步序图检查完毕。\n")
    return errors


######################
# 8 监控量测审核

# 监控点的布置间距
def rule_8_1(data_CAD):
    errors = []

    print("8.1 监控点布置间距检查开始...")

    if 'monitoringMeasurementLayoutPlan' in data_CAD and data_CAD['monitoringMeasurementLayoutPlan']:
        for filename, content in data_CAD['monitoringMeasurementLayoutPlan'].items():
            for monitor_name, values in content.items():
                if monitor_name in ['DBC', 'ZQC', 'ZQS', 'ZQT', 'ZCL', 'DSW']:
                    for value in values:
                        if value['value'] < 20 or value['value'] > 30:
                            error_ = {'file': filename, 'errorCode': 2006, 'errorTitle': '监控点间距不符合要求',
                                      'errorMsg': "{:s}间距不符合要求，图纸中间距为{:.0f}m, 允许的间距范围为20~30m!".format(monitor_name,
                                                                                                      value['value']),
                                      'path': value['bounding']}
                            log_error(error_, errors)
    else:
        error_ = {'file': '', 'errorCode': 411, 'errorTitle': '缺少监控量测图(monitoringMeasurementLayoutPlan)提取结果',
                  'path': []}
        log_error(error_, errors)
    print("8.1 监控点布置间距检查完毕。\n")
    return errors


def rule_8_2(data_CAD, list_of_content=None):
    errors = []

    print("8.2 监控剖面图检查开始...")

    # 获取 项目目录
    if 'table' in data_CAD and data_CAD['table']:
        tables_all = data_CAD['table']
    else:
        error_ = {'errorCode': 408, 'errorTitle': '缺少监控剖面图表格(monitoringMeasurementSection)提取结果', 'path': []}
        log_error(error_, errors)
        return errors

    # 获取监控测量相关的剖面图表格
    table_id = '-'
    for filename, file_id in list_of_content.items():
        if re.search(r'监控量测剖面图|监控量测断面图|施工监测剖面图', filename):
            table_id = list_of_content[filename]
    if table_id in tables_all:
        tableGroup = tables_all[table_id]['tableGroup']
    else:
        error_ = {'errorCode': 408, 'errorTitle': '缺少监控剖面图表格(monitoringMeasurementSection)提取结果', 'path': []}
        log_error(error_, errors)
        return errors

    # 检测频率
    # 基坑开挖深度-基坑设计深度
    freq_rule = {'≤5': {"≤5": "1次/1d", "5~10": "1次/2d", "10~15": "1次/3d", "15~20": "1次/3d", ">20": "1次/3d"},
                 '5~10': {"≤5": "--", "5~10": "1次/1d", "10~15": "1次/2d", "15~20": "1次/2d", ">20": "1次/2d"},
                 '10~15': {"≤5": "--", "5~10": "--", "10~15": "1次/1d", "15~20": "1次/1d", ">20": "1次/2d"},
                 '15~20': {"≤5": "--", "5~10": "--", "10~15": "--", "15~20": "（1次~2次）/1d", ">20": "（1次~2次）/1d"},
                 '>20': {"≤5": "--", "5~10": "--", "10~15": "--", "15~20": "--", ">20": "2次/1d"}
                 }


    # 获取CAD图纸表格中的监测频率
    freq_CAD = {}
    row_title = []
    col_title = []
    boundings = []
    count_1 = -1
    for table in tableGroup:
        boundings.append(table['bounding'])

    '''
    for table in tableGroup:
        count_1 = count_1 + 1
        if len(table['table']) < 2:
            continue
        if 'row' in table['table'][0]:
            row0 = table['table'][0]['row']
        else:
            continue


        if row0[0]['category'] == 'TEXT' and ''.join(row0[0]['data']) == '施工工况':  # 基于 '施工工况' 确定表格

            
            # # 审核表格完整性
            # try:
            #     if row0[1]['table'][0]['row'][0]['data'][0] != '基坑设计深度（m）':
            #         error_ = {'errorCode': 415, 'errorTitle': '基坑施工监测频率表错误', 'errorMsg': '列表头 "基坑设计深度（m）" 位置错误', 'path': []}
            #         log_error(error_, errors)
            # except IndexError:
            #     error_ = {'errorCode': 419, 'errorTitle': '基坑施工监测频率表错误', 'errorMsg': '缺少列表头 "基坑设计深度（m）"', 'path': []}
            #     log_error(error_, errors)
            # try:
            #     if row0[1]['table'][1]['row'][0]['table'][0]['row'][0]['data'][0] != '≤5':
            #         error_ = {'errorCode': 415, 'errorTitle': '基坑施工监测频率表错误', 'errorMsg': '列表头 "≤5" 位置错误', 'path': []}
            #         log_error(error_, errors)
            # except IndexError:
            #     error_ = {'errorCode': 419, 'errorTitle': '基坑施工监测频率表错误', 'errorMsg': '缺少列表头 "≤5"', 'path': []}
            #     log_error(error_, errors)
            # try:
            #     if row0[1]['table'][1]['row'][0]['table'][0]['row'][1]['data'][0] != '5~10':
            #         error_ = {'errorCode': 415, 'errorTitle': '基坑施工监测频率表错误', 'errorMsg': '列表头 "5~10" 位置错误', 'path': []}
            #         log_error(error_, errors)
            # except IndexError:
            #     error_ = {'errorCode': 419, 'errorTitle': '基坑施工监测频率表错误', 'errorMsg': '缺少列表头 "5~10"', 'path': []}
            #     log_error(error_, errors)
            # try:
            #     if row0[1]['table'][1]['row'][0]['table'][0]['row'][2]['data'][0] != '10~15':
            #         error_ = {'errorCode': 415, 'errorTitle': '基坑施工监测频率表错误', 'errorMsg': '列表头 "10~15" 位置错误', 'path': []}
            #         log_error(error_, errors)
            # except IndexError:
            #     error_ = {'errorCode': 419, 'errorTitle': '基坑施工监测频率表错误', 'errorMsg': '缺少列表头 "10~15"', 'path': []}
            #     log_error(error_, errors)
            # try:
            #     if row0[1]['table'][1]['row'][0]['table'][0]['row'][3]['data'][0] != '15~20':
            #         error_ = {'errorCode': 415, 'errorTitle': '基坑施工监测频率表错误', 'errorMsg': '列表头 "15~20" 位置错误', 'path': []}
            #         log_error(error_, errors)
            # except IndexError:
            #     error_ = {'errorCode': 419, 'errorTitle': '基坑施工监测频率表错误', 'errorMsg': '缺少列表头 "15~20"', 'path': []}
            #     log_error(error_, errors)
            # try:
            #     if row0[1]['table'][1]['row'][0]['table'][0]['row'][4]['data'][0] != '＞20':
            #         error_ = {'errorCode': 415, 'errorTitle': '基坑施工监测频率表错误', 'errorMsg': '列表头 "＞20" 位置错误', 'path': []}
            #         log_error(error_, errors)
            # except IndexError:
            #     error_ = {'errorCode': 419, 'errorTitle': '基坑施工监测频率表错误', 'errorMsg': '缺少列表头 "＞20"', 'path': []}
            #     log_error(error_, errors)

            if row0[1]['category'] == 'TABLE':
                row_level2 = row0[1]['table'][1]['row'][0]['table'][0]['row']
                for col_level2 in row_level2:
                    if col_level2['category'] == 'TEXT':
                        col_title.append(''.join(col_level2['data']))

            # 解析 第二行
            row1 = table['table'][1]['row']

            for col_level3 in row1[0]['table'][0]['row'][1]['table']:
                if col_level3['row'][0]['category'] == 'TEXT':
                    row_title.append(''.join(col_level3['row'][0]['data']))

            for row_id3, row_level3 in enumerate(row1[1]['table']):
                temp_dict = {}
                for col_id4, col_level4 in enumerate(row_level3['row']):
                    temp_dict[col_title[col_id4]] = ''.join(col_level4['data'])

                freq_CAD[row_title[row_id3]] = temp_dict
                '''

    for table in tableGroup:
        count_1 = count_1 + 1
        if len(table['table']) < 2:
            continue
        if 'row' in table['table'][0]:
            row0 = table['table'][0]['row']
        else:
            continue

        print('table'+str(count_1))

        if row0[0]['category'] == 'TEXT' and ''.join(row0[0]['data']) == '施工工况':  # 基于 '施工工况' 确定表格
            tableArray = list()
            tempdata = list()
            full_data_flag=0
            full_data = ''
            for rowInTable in table['table']:
                #print(len(rowInTable['row']))
                for tableData in rowInTable['row']:
                    #print(str(tableData['data']))
                    if len(tableData['data'])>1:  #如果小智读取的一格数组里有多个项，进行拼接
                        for tableData_array in tableData['data']:
                            full_data+=tableData_array
                            full_data_flag=1
                    elif len(tableData['data'])<1:
                        tempdata.append('--')
                        continue
                    if full_data_flag:  #如果是多个拼接，按object加入临时列表
                        tempdata.append(full_data)
                        full_data=''
                        full_data_flag=0
                    else:
                        if ''.join(tableData['data'])=='-':
                            tempdata.append('--')
                            continue
                        tempdata.extend(tableData['data'])
                        #print(type(tableData['data']))
                tableArray.append(tempdata)
                tempdata=list()
                    #tableArray.append(str(tableData['data']))
                #tablearray=np.array[len(rowInTable['row'])][len(table['table'])]
            tableArray = np.reshape(tableArray, (len(table['table']),len(rowInTable['row']))) #转成与图纸一样的表格
            freq_CAD=pd.DataFrame(tableArray)  #将表格放入dataframe便于处理


            freq_CAD.drop(freq_CAD.head(1).index,inplace=True)
            freq_CAD.drop(freq_CAD.tail(1).index,inplace=True)
            freq_CAD.drop(columns=0,inplace=True)
            #freq_CAD = freq_CAD.iloc[1:,1:1]
            #print(freq_CAD)
            #freq_CAD.index = freq_CAD.iloc[0].values
            #new_header = freq_CAD.iloc[0]  # grab the first row for the header
            #new_header = new_header.iloc[1:]
            #print(new_header)
            freq_CAD = freq_CAD[1:]  # take the data less the header row
            print(freq_CAD)
            #freq_CAD.columns = new_header  # set the header row as the df header
            freq_CAD = freq_CAD.iloc[: , 1:]
            #new_index = freq_CAD.iloc[:,0]

            #print(new_index)
            #freq_CAD = freq_CAD.tail(len(rowInTable['row'])-1)


            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print(freq_CAD)
            print(freq_CAD.axes)
            freq_rule = pd.DataFrame(freq_rule)

            freq_rule = freq_rule.T
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            print(freq_rule)
            print(freq_CAD.axes)
            '''
            if freq_CAD.empty:
                error_ = {'errorCode': 419, 'errorTitle': '缺少基坑施工监测频率表', 'errorMsg': '缺少基坑施工监测频率表', 'path': []}
                log_error(error_, errors)
            else:
                # compare freq_CAD with freq_rule
                for row_name, row_value in freq_CAD.items():
                    for col_name, col_value in row_value.items():
                        if row_name in freq_rule and col_name in freq_rule[row_name]:
                            if re.search(r'\d', freq_CAD[row_name][col_name]) and re.search(r'\d', freq_rule[row_name][col_name]) and (freq_CAD[row_name][col_name] != freq_rule[row_name][col_name]):
                                error_ = {'file': table_id, 'errorCode': 2005, 'errorTitle': '图纸与规范不符', 'errorMsg': "{:s} {:s} 的值 与规范不一致, 图纸中为：{:s}，规范中为：{:s}".format(row_name, col_name, freq_CAD[row_name][col_name], freq_rule[row_name][col_name]), 'path': boundings[count_1]}
                                log_error(error_, errors)'''
            if freq_CAD.empty:
                error_ = {'errorCode': 419, 'errorTitle': '缺少基坑施工监测频率表', 'errorMsg': '缺少基坑施工监测频率表', 'path': []}
                log_error(error_, errors)
            else:
                freq_CAD = np.array(freq_CAD)
                freq_rule = np.array(freq_rule)
                c = (freq_CAD == freq_rule)
                if not isinstance(c,np.ndarray):
                    if not c:
                        if freq_CAD.shape[0] < freq_rule.shape[0]:
                            error_ = {'file': table_id, 'errorCode': 2005, 'errorTitle': '图纸与规范不符',
                                      'errorMsg': "缺少{:d}米后的基坑开挖深度".format(
                                          freq_CAD.shape[0] * 5),
                                      'path': boundings[count_1]}
                            log_error(error_, errors)
                        if freq_CAD.shape[1] < freq_rule.shape[1]:
                            error_ = {'file': table_id, 'errorCode': 2005, 'errorTitle': '图纸与规范不符',
                                      'errorMsg': "缺少{:d}米后的基坑设计深度".format(
                                          freq_CAD.shape[1] * 5),
                                      'path': boundings[count_1]}
                            log_error(error_, errors)
                elif not c.all():
                    for idx in np.argwhere(c == 0):
                        # print(idx)
                        #print(type(idx))

                        idx_x, idx_y = np.split(idx, 2)

                        '''
                        #print(type(freq_CAD[idx_x, idx_y].tobytes()))
                        #cad_waitToCompare=freq_CAD[idx_x, idx_y].tostring()
                        temp1=freq_CAD[idx_x, idx_y].tolist()[0]                    #[0]
                        temp1=strQ2B(temp1)
                        
                        temp2='(1~2次)/1d'
                        temp3=freq_CAD[idx_x, idx_y]
                        with open("11.txt","w") as f:
                            f.write(temp2)
                        print(temp3)
                        testflag=0
                        if temp1.strip()==temp2.strip():
                            testflag=1
                        print(testflag)
                        
                        print(chardet.detect(temp3))
                        print(chardet.detect(temp2.encode()))
                        '''
                        '''
                        for i in range(len(temp1)):
                            print(str(ord(temp1[i])))
                        print('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq')
                        for i in range(len(temp2)):
                            print(str(ord(temp2[i])))

                        #tempa=re.search("\d次~\d次",bytes.decode(freq_CAD[idx_x, idx_y].tostring())).group(1)
                        #matchObj=re.search("(\d)?[\~\-](\d)次",temp3.decode('utf-8','ignore'))
                        #matchObj = re.search("(\d)?[\~\-](\d)次", temp3.decode('ISO-8859-1'))
                        #matchObj = re.search(rb"(\d)?[\~\-](\d)次", temp2.decode())
                        #matchObj = re.search("(\d)?[\~\-](\d)次", temp1)
                        '''
                        matchObj = re.search("(\d)?[\~\-](\d)次", strQ2B(freq_CAD[idx_x, idx_y].tolist()[0]))
                        if matchObj.group(1)=='1' and matchObj.group(2)=='2':
                            continue
                        # print(type(freq_CAD[int(idx_x)][int(idx_y)]))
                        # print(type(freq_rule[int(idx_x)][int(idx_y)]))
                        error_ = {'file': table_id, 'errorCode': 2005, 'errorTitle': '图纸与规范不符',
                                  'errorMsg': "第{:s}行 第{:s}列 的值 与规范不一致, 图纸中为：{:s}，规范中为：{:s}".format(
                                      np.array2string(idx_x[0] + 1), np.array2string(idx_y[0] + 1),
                                      freq_CAD[int(idx_x)][int(idx_y)], freq_rule[int(idx_x)][int(idx_y)]),
                                  'path': boundings[count_1]}
                        log_error(error_, errors)



        # 明挖监控量测表
        if row0[0]['category'] == 'TEXT' and ''.join(row0[0]['data']) == '序号':
            tableArray = list()
            tempdata = list()
            full_data_flag = 0
            full_data = ''
            for rowInTable in table['table']:
                # print(len(rowInTable['row']))
                for tableData in rowInTable['row']:
                    # print(str(tableData['data']))
                    if len(tableData['data']) > 1:  # 如果小智读取的一格数组里有多个项，进行拼接
                        for tableData_array in tableData['data']:
                            full_data += tableData_array
                            full_data_flag = 1
                    elif len(tableData['data'])<1:
                        tempdata.append('--')
                        continue
                    if full_data_flag:  # 如果是多个拼接，按object加入临时列表
                        tempdata.append(full_data)
                        full_data = ''
                        full_data_flag = 0
                    else:
                        tempdata.extend(tableData['data'])
                tableArray.append(tempdata)
                tempdata = list()
                # tableArray.append(str(tableData['data']))
                # tablearray=np.array[len(rowInTable['row'])][len(table['table'])]
            flag_failed=0
            try:
                tableArray = np.reshape(tableArray, (len(table['table']), len(rowInTable['row'])))  # 转成与图纸一样的表格
                freq_CAD = pd.DataFrame(tableArray)
            except:
                flag_failed=1
            if flag_failed:
                error_ = {'errorCode': 420, 'errorTitle': '明挖监控量测表格式异常', 'errorMsg': '明挖监控量测表格式异常,请检查提取是否有特殊符号不识别', 'path': []}
                log_error(error_, errors)
            elif freq_CAD.empty and not flag_failed:
                error_ = {'errorCode': 420, 'errorTitle': '缺少明挖监控量测表', 'errorMsg': '缺少明挖监控量测表', 'path': []}
                log_error(error_, errors)
            else:
                # print(np.argwhere(tableArray == '地表沉降'))
                flag_Landsubsidence,flag_VerticalDisplacement,flag_HorizontalDisplacement,flag_ControlStandard=0,0,0,0
                if np.argwhere(tableArray == '地表沉降').any():
                    idx_Landsubsidence_x, idx_Landsubsidence_y = np.argwhere(tableArray == '地表沉降')[0]
                    flag_Landsubsidence=1
                if np.argwhere(tableArray == '桩顶竖向位移').any():
                    idx_VerticalDisplacement_x, idx_VerticalDisplacement_y = np.argwhere(tableArray == '桩顶竖向位移')[0]
                    flag_VerticalDisplacement=1
                if np.argwhere(tableArray == '桩顶水平位移').any():
                    idx_HorizontalDisplacement_x, idx_HorizontalDisplacement_y = np.argwhere(tableArray == '桩顶水平位移')[0]
                    flag_HorizontalDisplacement=1
                if np.argwhere(tableArray == '变形控制标准').any():
                    idx_ControlStandard_x, idx_ControlStandard_y = np.argwhere(tableArray == '变形控制标准')[0]
                    flag_ControlStandard=1

                if flag_Landsubsidence and flag_ControlStandard:
                    # 地表沉降变形控制标准判断
                    print(type(tableArray[idx_Landsubsidence_x, idx_ControlStandard_y]))
                    all_outOfBound_list=re.findall("(\d\d)mm", tableArray[idx_Landsubsidence_x, idx_ControlStandard_y])
                    for i in all_outOfBound_list:
                        if (int(i) > 30
                                or int(i) < 20):
                            error_ = {'file': table_id, 'errorCode': 2005, 'errorTitle': '图纸与规范不符',
                                      'errorMsg': "地表沉降变形控制标准与规范不一致, 图纸中为：{:s}，应>=20且<=30".format(i),
                                      'path': boundings[count_1]}
                            log_error(error_, errors)

                if flag_VerticalDisplacement and flag_ControlStandard:
                    # 桩顶竖向位移判断
                    all_outOfBound_list = re.findall("(\d\d)mm", tableArray[idx_VerticalDisplacement_x, idx_ControlStandard_y])
                    for i in all_outOfBound_list:
                        if (int(i) != 10):
                            error_ = {'file': table_id, 'errorCode': 2005, 'errorTitle': '图纸与规范不符',
                                      'errorMsg': "桩顶竖向位移与规范不一致, 图纸中为：{:s}，应为10mm".format(i),
                                      'path': boundings[count_1]}
                            log_error(error_, errors)

                if flag_HorizontalDisplacement and flag_ControlStandard:
                    # 桩顶水平位移判断
                    all_outOfBound_list = re.findall("(\d\d)mm", tableArray[idx_HorizontalDisplacement_x, idx_ControlStandard_y])
                    for i in all_outOfBound_list:
                        if (int(i) != 10):
                            error_ = {'file': table_id, 'errorCode': 2005, 'errorTitle': '图纸与规范不符',
                                      'errorMsg': "桩顶水平位移与规范不一致, 图纸中为：{:s}，应为10mm".format(i),
                                      'path': boundings[count_1]}
                            log_error(error_, errors)


                '''freq_rule = np.array([
                                        ['序号','监测项目','监测仪器及元件','测点布置','监测精度','变形控制标准','监测频率'],
                                        ['1','基坑及其周围环境观察','--','对开挖后的工程地质及水文地质的观察记录（地层、节理裂隙形态及充填性、含水情况等）;支护裂隙和支护状态的观察描述;邻近建（构）筑物及地面的变形、裂缝等的观察描述。','--','--','全过程，1次/天，情况异常时加密监测频率。'],
                                        ['2','地表沉降','水准仪','平面布置见监控量测平面图，纵向每20m左右一个监测断面，基坑每侧2个监测点;主监测断面80m一个，基坑每侧4个监测点;','%%P0.3mm','30mm,变化速率2mm/d','详见本图《基坑施工监测频率表》 '],
                                        ['3','桩顶竖向位移','水准仪','横向布置如图，纵向每20m左右一监测断面。','%%P0.3mm','10mm,变化速率1mm/d', '详见本图《基坑施工监测频率表》 '],
                                        ['4','桩顶水平位移','经纬仪或全站仪','横向布置如图，纵向每20m左右一监测断面。','%%P0.3mm', '10mm,变化速率2mm/d','详见本图《基坑施工监测频率表》 '],
                                        ['5','桩体水平位移','测斜仪','横向布置如图，纵向每40m左右一监测断面。沿桩竖直方向上间距为1m，监测总深度为桩长。','0.02mm/0.5m','30mm,变化速率2mm/d','详见本图《基坑施工监测频率表》 '],
                                        ['6','支撑轴力','应变计、轴力计、频率接收仪','横向布置如图，纵向每40m左右一监测断面。','0.15%%%F.s', '详见钢支撑轴力表','详见本图《基坑施工监测频率表》 '],
                                        ['7','地下水位','电测水位计、PVC管','横向布置如图，纵向每40m左右一监测断面。','5.0mm','基坑底以下1m，0.5m/d', '1次/（1~2）天']
                                    ])'''








    count_2 = -1
    # 判断测斜仪精度符不符合要求
    # 直接用正则表达式匹配 0.02mm/0.5m 的格式
    for table in tableGroup:
        count_2 = count_2 + 1
        all_data = recursive_add(table)
        cexieyi_acc = re.search(r'(\d+\.\d+)mm/(\d+\.\d+)?m', all_data)
        if cexieyi_acc:
            print(cexieyi_acc.group(2))
            if len(cexieyi_acc.regs) == 3 and cexieyi_acc.group(2) == None:
                if float(cexieyi_acc.group(1)) > 0.25:
                    error_ = {'file': table_id, 'errorCode': 2005, 'errorTitle': '图纸与规范不符',
                              'errorMsg': "测斜仪精度为 {:s}mm/m, 低于规定的 0.25mm/1m".format(cexieyi_acc.group(1),
                                                                                        cexieyi_acc.group(2)),
                              'path': boundings[count_2]}
                    log_error(error_, errors)
            elif len(cexieyi_acc.regs) == 3 and float(cexieyi_acc.group(2)) == 0.5:
                if float(cexieyi_acc.group(1)) * 2 > 0.25:
                    print("测斜仪精度为 {:s}mm/{:s}m, 低于规定的 0.25mm/1m".format(cexieyi_acc.group(1), cexieyi_acc.group(2)))
                    error_ = {'file': table_id, 'errorCode': 2005, 'errorTitle': '图纸与规范不符',
                              'errorMsg': "测斜仪精度为 {:s}mm/{:s}m, 低于规定的 0.25mm/1m".format(cexieyi_acc.group(1),
                                                                                        cexieyi_acc.group(2)),
                              'path': boundings[count_2]}
                    log_error(error_, errors)
            else:
                if float(cexieyi_acc.group(1)) > 0.25:
                    error_ = {'file': table_id, 'errorCode': 2005, 'errorTitle': '图纸与规范不符',
                              'errorMsg': "测斜仪精度为 {:s}mm/{:s}m, 低于规定的 0.25mm/1m".format(cexieyi_acc.group(1),
                                                                                        cexieyi_acc.group(2)),
                              'path': boundings[count_2]}
                    log_error(error_, errors)

    # 判断竖向间距有缺少标注
    if 'monitoringMeasurementSection' in data_CAD and data_CAD['monitoringMeasurementSection']:
        for filename, content in data_CAD['monitoringMeasurementSection'].items():
            if 'mark' in content:
                if content['mark'] and len(content['mark']) == 2:
                    for mark in content['mark']:
                        if mark['value'] and re.search(r'\d+\.\d+m|\dm', mark['value']):
                            distance = re.search(r'\d+\.\d+|\d',
                                                 re.search(r'\d+\.\d+m|\dm', mark['value']).group(0)).group(0)
                            if float(distance) != 1:
                                error_ = {'file': filename, 'errorCode': 2012, 'errorTitle': '监测点的竖向布置间距不符合要求',
                                          'errorMsg': "监测点的竖向布置间距不符合要求,图纸中为{:s}m,标准为1m".format(distance),
                                          'path': mark['bounding']}
                                log_error(error_, errors)
                        else:
                            error_ = {'file': filename, 'errorCode': 415, 'errorTitle': '缺少标注监测点的竖向布置间距',
                                      'errorMsg': "缺少标注监测点的竖向布置间距", 'path': []}
                            log_error(error_, errors)
                else:
                    error_ = {'file': filename, 'errorCode': 415, 'errorTitle': '缺少标注监测点的竖向布置间距',
                              'errorMsg': "缺少标注监测点的竖向布置间距", 'path': []}
                    log_error(error_, errors)
            else:
                error_ = {'file': filename, 'errorCode': 415, 'errorTitle': '缺少标注监测点的竖向布置间距',
                          'errorMsg': "缺少标注监测点的竖向布置间距", 'path': []}
                log_error(error_, errors)
    else:
        error_ = {'file': '', 'errorCode': 412, 'errorTitle': '缺少监控量测图(monitoringMeasurementSection)提取结果',
                  'path': []}
        log_error(error_, errors)





    print("8.2 监控剖面图检查完毕。\n")
    return errors


# 10.1 设计依据，检查版本是不是最新
def rule_10_1(data, regus):
    # data: dict, 计算书提取的规范字典
    # regus: dict, 所有规范
    errors = []

    print("10.1 设计依据检查开始...")

    if '设计依据' not in data:
        error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整', 'errorMsg': "请核对计算书设计规范", 'path': []}
        log_error(error_, errors)

    for i, item in enumerate(data['设计依据']):
        segments = item.split('（')
        seg_name = segments[0]

        if seg_name not in regus:
            continue

        if len(segments) > 1:  # 有版本的规范
            flag = False
            seg_version = segments[1].split('）')[0]
            seg_version = re.sub(r' ', '', seg_version)
            reg_versions = regus[seg_name]
            reg_version = None
            for reg_version in reg_versions:
                if seg_version == reg_version:
                    flag = True

            if not flag:
                error_ = {'file': '计算书', 'errorCode': 1001, 'errorTitle': '计算书中信息错误',
                          'errorMsg': "规范 （{:d}）{:s} 版本号不对，计算书版本号：{:s}, 规范库版本号：{:s}".format(i + 1, seg_name,
                                                                                            seg_version,
                                                                                            reg_version), 'path': []}
                log_error(error_, errors)

    print("10.1 设计依据检查完毕。\n")
    return errors


# 10.2 计算参数
def rule_10_2(data):
    errors = []
    print("10.2 计算参数检查开始...")
    if ("荷载参数" not in data) or ("20kPa" not in data['荷载参数']):
        error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整', 'errorMsg': "请核对荷载参数说明", 'path': []}
        log_error(error_, errors)

    print("10.2 计算参数检查完毕。\n")
    return errors


# 10.4 设计标准，判断三个条目是否都在
def rule_10_4(data):
    # data: dict, 计算书提取的字典
    errors = []

    print("10.4 设计依据检查开始...")

    # check if 10.4.1 exists
    # if '设计标准' not in data or '地下结构的基坑支护结构' not in data['设计标准']:
    #     error_={}
    #     error_['file']='计算书'
    #     error_['errorCode']=1002
    #     error_['errorTitle']='计算书中缺少必要信息'
    #     error_['errorMsg']="缺少 地下结构的基坑支护结构 的说明"
    #     log_error(error_,errors)

    if '设计标准' not in data or '地下结构应按抗浮设防水位进行抗浮稳定性验算' not in data['设计标准']:
        error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整', 'errorMsg': "请核对计算书中 地下结构抗浮稳定性验算的设计标准 的说明",
                  'path': []}
        log_error(error_, errors)

    if '设计标准' not in data or '砂性土地层' not in data['设计标准']:
        error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整', 'errorMsg': "请核对计算书中 地层参数设计标准 的说明",
                  'path': []}
        log_error(error_, errors)

    print("10.4 设计标准检查完毕。\n")
    return errors


# 10.5 支护结构计算
def rule_10_5(data):
    sec_name = None
    errors = []
    print("10.5 支护结构计算 审查开始...")

    if '钢支撑计算' not in data or not data['钢支撑计算']:
        error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整', 'errorMsg': "请核对计算书中钢支撑计算结果", 'path': []}
        log_error(error_, errors)
        return errors

        # 10.5.1 钢支撑计算
    items = ['刚度', '强度', '稳定性', '挠度']
    for sec_name, content in data['钢支撑计算'].items():
        for item_name in items:
            if item_name in content and content[item_name]:
                error_ = check_item(content, item_name, sec_name)
                if error_:
                    error_['file'] = '计算书'
                    error_['path'] = []
                    log_error(error_, errors)
            else:
                error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整',
                          'errorMsg': "请核对计算书中 {:s}钢支撑{:s} 信息".format(sec_name, item_name), 'path': []}
                log_error(error_, errors)

    # 10.5.3 钢腰梁及连系梁计算
    if '钢腰梁及连系梁计算' not in data or not data['钢腰梁及连系梁计算']:
        error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整', 'errorMsg': "请核对计算书中钢腰梁及连系梁计算结果",
                  'path': []}
        log_error(error_, errors)
        return errors

    items = ['抗弯', '抗剪', '挠度']
    content = data['钢腰梁及连系梁计算']
    for item_name in items:
        if item_name in content and content[item_name]:
            error_ = check_item(content, item_name, sec_name)
            if error_:
                error_['file'] = '计算书'
                error_['path'] = []
                log_error(error_, errors)
        else:
            error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整',
                      'errorMsg': "请核对计算书中钢腰梁及连系梁{:s}验算信息".format(item_name), 'path': []}
            log_error(error_, errors)

    print("10.5 支护结构计算 审查完毕。\n")

    return errors


# 10.6 工程材料信息
def rule_10_6(data):
    errors = []
    steel_levels = ['HPB300', 'HRB400', 'HRB335']
    steel_types = ['Q235', 'Q345']

    print("10.6 工程材料信息 审查开始...")
    if ('钢筋等级' not in data) or (not check_words(steel_levels, ''.join(data['钢筋等级']))):
        error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整', 'errorMsg': "钢筋等级未标", 'path': []}
        log_error(error_, errors)

    if ('型号钢' not in data) or (not check_words(steel_types, ''.join(data['型号钢']))):
        error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整', 'errorMsg': "钢筋型号未标", 'path': []}
        log_error(error_, errors)

    print("10.6 工程材料信息 审查完毕。\n")

    return errors


# 10.7 抗浮计算
def rule_10_7(data):
    errors = []
    print("10.7 抗浮计算 审查开始...")
    if '抗浮计算' in data and data['抗浮计算']:
        if '不满足' in data['抗浮计算']:
            error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中验算结果不满足要求', 'errorMsg': "抗浮计算不满足要求",
                      'path': []}
            log_error(error_, errors)
    else:
        error_ = {'file': '计算书', 'errorCode': 1002, 'errorTitle': '计算书中信息表达不完整', 'errorMsg': "缺少 抗浮计算 说明", 'path': []}
        log_error(error_, errors)

    print("10.7 抗浮计算 审查完毕。\n")
    return errors


if __name__ == '__main__':
    # path_target为系统的绝对路径
    report = {}  # 最终反馈的报告

    path_current = os.getcwd()
    # path_target = os.path.join(path_current, "图纸/磁各庄站")
    # path_target = os.path.join(path_current, "图纸/积水潭站")
    # path_target=os.path.join(path_current, "图纸/金安桥站")
    # path_target = os.path.join(path_current, "图纸/磁各庄站2")

    if path_target is None:
        print("请输入正确的文件目录：")
        print(None)
    ####################
    # 读取规范
    path_regu = "./regulations/规范、标准.txt"
    regus = read_regulation(path_regu)

    if not regus:  # 不能读取规范
        report['code'] = 201
        report['msg'] = '不能读取规范'
        report['data'] = {}
        print(report)

    ####################
    # 读取计算书
    path_calc = os.path.join(path_target, "calculations")
    formats = {}  # used to indicate whether the file is found, first find .docx, if not find .doc
    for filename in os.listdir(path_calc):
        if not re.search("^~", filename):
            if filename.endswith("docx"):
                formats['docx'] = filename
            elif filename.endswith("doc"):
                formats['doc'] = filename

    if 'docx' in formats:
        filename_calc = os.path.join(path_calc, formats['docx'])
    elif 'doc' in formats:
        filename_calc = os.path.join(path_calc, formats['doc'])
    else:
        filename_calc = None
        report['code'] = 202
        report['msg'] = '不能读取计算书'
        report['data'] = {}
        print(report)

    # 判断计算书的格式，如果是.doc结尾的话转为.docx格式
    if filename_calc and filename_calc.endswith(".doc"):
        doc2docx(filename_calc)
        filename_calc = filename_calc[:-3] + "docx"

    data_calc = read_calculation(filename_calc)

    if not data_calc:  # 不能读取计算书
        report['code'] = 202
        report['msg'] = '不能读取计算书'
        report['data'] = {}
        print(report)

    ##########################
    # 读取CAD识图结果
    path_CAD_results = os.path.join(path_target, "extractions")

    # 读取识图结果
    data_CAD = read_CAD_results(path_CAD_results)

    if not data_CAD:  # 不能读取识图结果
        report['code'] = 203
        report['msg'] = '不能读取识图结果'
        report['data'] = {}
        print(report)

    # 获取目录
    list_of_content = obtain_list_of_content(data_CAD)
    if not list_of_content:  # 不能读取图纸目录
        report['code'] = 204
        report['msg'] = '不能读取图纸目录'
        report['data'] = {}
        print(report)
    all_errors = []
    ###########################
    errors = rule_7_1(data_CAD)
    all_errors.extend(errors)

    # 整理返回结果
    report['code'] = 200
    report['msg'] = '正常返回'

    data = {'checkId': -1, 'result': all_errors}
    report['data'] = data

    print(report)
