import pandas as pd  # 导入pandas包

data = pd.read_csv("1.csv")  # 读取csv文件
print(data)  # 打印所有文件
print(data.head(5))
print(data.columns)
print(data.loc[[1, 4], ['基坑设计深度']])
