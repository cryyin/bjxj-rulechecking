import requests

# import json
# url = "http://39.97.225.186:8010"
url = "http://localhost:8010"
files = {'zip_file': open('E:\\Projects\\智能审图\\识图结果\\NEW\\jinanqiao.zip', 'rb')}
data = {"key": "znst20210505", "checkId": "503447"}
res = requests.post(url=url, files=files, data=data)
print(res.text)
