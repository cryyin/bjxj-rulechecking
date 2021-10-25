# rule_checking

# 返回 code
code={
    200: '正常反馈结果',
    205: '密码错误',
    206: '正在提取中',
    207: '无效checkId',
    208: '没有上传zip文件'
}

# 警告类型
warning_type={
    401: "缺少CAD(extractions)提取结果",
    402: "缺少计算书(calculations)提取结果",
    403: "缺少CAD图纸目录表格(directory)提取结果",
    404: "缺少规范文件(regulations)",
    405: "缺少平面图(enclosureStructureLayoutPlan)提取结果",
    406: "缺少总说明(designDescription)提取结果",
    407: '缺少剖面图(enclosureStructureCrossSection)提取结果',
    408: '缺少监控剖面图表格(monitoringMeasurementSection)提取结果',
    409: '缺少内支撑详图(enclosureStructureDetailDrawing)提取结果',
    410: '缺少施工步序图(constructionSteps)提取结果',
    411: '缺少监控量测图(monitoringMeasurementLayoutPlan)提取结果',
    412: '缺少监控量测图(monitoringMeasurementSection)提取结果',
    413: '缺少钢支撑轴力值表格(enclosureStructureCrossSection)提取结果',
    414：'缺少部分CAD(extractions)提取结果',
    415: '缺少标注监测点的竖向布置间距',
    416: '图纸中缺少必要信息(桩径)',
    417: '图纸中缺少必要信息(钻孔灌注桩标注)'
    418：'CAD图纸中缺少嵌固深度'
    419: '缺少基坑施工监测频率表'
    420: '缺少明挖监控量测表'
}

# 错误类型
error_type={
    1001: "计算书中信息错误",
    1002: '计算书中缺少必要信息',
    2001: "桩径不满足要求",
    2002: '桩间净距不满足要求', 
    2003: '支护间距不满足要求',
    2004: '设计总说明缺少必要描述',
    2005: '图纸与规范不符',
    2006: '监控点间距不符合要求',
    2009: '图纸中缺少肋板、抗剪措施',
    2010: '钢支撑未见防脱落措施',
    2011: '图纸中缺少法兰盘'
    2012: '监测点的竖向布置间距不符合要求'
    3001: '补充必要的验算',
    3002: '图纸与计算书信息不符',
}