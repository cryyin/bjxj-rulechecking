# main file for reading and checking
from rules import *
from read_items import *
from utils import *
import configparser
import pandas as pd


def main_check(path_target=None, checkId=-1):
    states = {'calc': True, 'cad': True, 'list': True, 'regus': True,'openFailed':True}
    path_current = os.getcwd()
    # path_target为系统的绝对路径
    report = {}  # 最终反馈的报告

    conf = configparser.ConfigParser()
    conf.read(path_current + '/app.conf')  # 文件路径
    path_target_flag = conf.get("env", "state")  # 获取指定section 的option值
    print(path_target_flag)
    if (path_target_flag=='dev'):
        # path_target = os.path.join(path_current, "图纸/磁各庄站")
        # path_target = os.path.join(path_current, "图纸/积水潭站")
        # path_target = os.path.join(path_current, "图纸/金安桥站")
        # path_target = os.path.join(path_current, "图纸/西洼地站")
         path_target = os.path.join(path_current, "图纸/测试")

    if path_target is None:
        print("请输入正确的文件目录：")
        return None
    ####################
    # 读取规范
    path_regu = "./regulations/规范、标准.txt"
    regus = read_regulation(path_regu)

    if not regus:  # 不能读取规范
        states['regus'] = False
    ####################
    # 读取计算书
    path_calc = os.path.join(path_target, "calculations")
    formats = {}  # used to indicate whether the file is found, first find .docx, if not find .doc
    if os.path.exists(path_calc):
        for filename in os.listdir(path_calc):
            if not re.match("^~", filename):
                if filename.endswith("docx"):
                    formats['docx'] = filename
                elif filename.endswith("doc"):
                    formats['doc'] = filename
        filename_calc = None
        if 'docx' in formats:
            filename_calc = os.path.join(path_calc, formats['docx'])
        elif 'doc' in formats:
            filename_calc = os.path.join(path_calc, formats['doc'])
        else:
            states['calc'] = False

        # 判断计算书的格式，如果是.doc结尾的话转为.docx格式
        if filename_calc and filename_calc.endswith(".doc"):
            doc2docx(filename_calc)
            filename_calc = filename_calc[:-3] + "docx"

        data_calc = None
        if filename_calc:
            data_calc = read_calculation(filename_calc)
            if data_calc=='open failed':
                states['openFailed']=False

        if not data_calc:  # 不能读取计算书
            states['calc'] = False
    else:
        states['calc'] = False



    ##########################
    # 读取CAD识图结果
    path_CAD_results = os.path.join(path_target, "extractions")

    # 读取识图结果
    data_CAD = read_CAD_results(path_CAD_results)

    if not data_CAD:  # 不能读取识图结果
        states['cad'] = False

    # 获取目录
    list_of_content = obtain_list_of_content(data_CAD)
    print(list_of_content)
    if not list_of_content:  # 不能读取图纸目录
        states['list'] = False

    all_errors = []
    ###########################
    # 判断缺少错误
    errors = []
    if not states['cad']:
        error_ = {'file': 'extractions', 'errorCode': 401, 'errorTitle': '缺少CAD(extractions)提取结果', 'path': []}
        log_error(error_, errors)
    if not states['calc']:
        error_ = {'file': 'calculations', 'errorCode': 402, 'errorTitle': '缺少计算书(calculations)提取结果', 'path': []}
        log_error(error_, errors)
    if not states['openFailed']:
        error_ = {'file': 'calculations', 'errorCode': 421, 'errorTitle': '计算书(calculations)打开失败', 'path': []}
        log_error(error_, errors)
        states['calc']=False
    if not states['list']:
        error_ = {'file': 'directory', 'errorCode': 403, 'errorTitle': '缺少CAD图纸目录(directory)提取结果', 'path': []}
        log_error(error_, errors)
    if not states['regus']:
        error_ = {'file': 'regulations', 'errorCode': 404, 'errorTitle': '缺少规范文件(regulations)', 'path': []}
        log_error(error_, errors)

    ###########################
    # 对照目录判断缺少文件
    checkFiles=set(list_of_content.values())
    print('###############################################')
    #print(checkFiles)
    #print(data_CAD.keys())
    #print(data_CAD['constructionSteps'].keys())
    for dirname in data_CAD.keys():
        for file_in_dir in data_CAD[dirname].keys():
            checkFiles.discard(file_in_dir)

    #checkFiles.discard(str(data_CAD['constructionSteps'].keys()))
    print('未检测到以下图纸：'+str(checkFiles))
    for filename_print in checkFiles:
        error_ = {'file': str(filename_print), 'errorCode': 414, 'errorTitle': '缺少部分CAD(extractions)提取结果','path': []}
        log_error(error_, errors)

    all_errors.extend(errors)

    #for filenames_of_cad in data_CAD


    ###########################
    # 第三章 平面图审核
    # 3.3 判断桩径、桩间距、支撑间距满不满足要求
    if states['cad'] and states['calc']:
        errors = rule_3_3(data_CAD, data_calc)
        all_errors.extend(errors)

    #############################
    # 第四章 剖面图审核
    # 4.1 地下水位
    if states['cad']:
        errors = rule_4_1(data_CAD)
        all_errors.extend(errors)

    # 4.3 嵌固深度
    if states['cad'] and states['calc']:
        errors = rule_4_3(data_CAD, data_calc)
        all_errors.extend(errors)

    # 4.4 钢支撑轴力值
    if states['cad'] and states['calc'] and states['list']:
        errors = rule_4_4(data_CAD, data_calc, list_of_content)
        all_errors.extend(errors)

    # 4.6 挡墙验算
    if states['cad'] and states['calc']:
        errors = rule_4_6(data_CAD, data_calc)
        all_errors.extend(errors)

    ######################################
    # 第六章 内支撑详图审查
    if states['cad']:
        errors = rule_6(data_CAD)
        all_errors.extend(errors)

    ###########################
    # 第七章 施工步序图审核
    # 7.1 与计算工况是否一致建议人工复核
    if states['cad']:
        errors = rule_7_1(data_CAD)
        all_errors.extend(errors)

    ###########################
    # 第八章 监控测量审核
    # 8.1 监测点布置距离
    if states['cad']:
        errors = rule_8_1(data_CAD)
        all_errors.extend(errors)

    # 8.2 剖面图
    if states['cad'] and states['calc']:
        errors = rule_8_2(data_CAD, list_of_content)
        all_errors.extend(errors)

    ###########################
    # 第十章 计算书审核
    # 10.1 设计依据
    if states['regus'] and states['calc']:
        errors = rule_10_1(data_calc, regus)
        all_errors.extend(errors)

    # 10.2 计算参数
    if states['calc']:
        errors = rule_10_2(data_calc)
        all_errors.extend(errors)

    # 10.4 设计标准
    if states['calc']:
        errors = rule_10_4(data_calc)
        all_errors.extend(errors)

    # 10.5 支护结构计算
    if states['calc']:
        errors = rule_10_5(data_calc)
        all_errors.extend(errors)

    # 10.6 工程材料信息
    if states['calc']:
        errors = rule_10_6(data_calc)
        all_errors.extend(errors)

    # 10.7 抗浮计算
    if states['calc']:
        errors = rule_10_7(data_calc)
        all_errors.extend(errors)

    # 整理返回结果
    report['code'] = 200
    report['msg'] = '正常返回'

    data = {'checkId': checkId, 'result': all_errors}
    report['data'] = data

    return report


if __name__ == '__main__':
    report = main_check()
    print(report)
