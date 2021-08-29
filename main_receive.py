#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
import os
import time
import zipfile
from abc import ABC

import tornado.ioloop
import tornado.web

from check import main_check

os.path.altsep = '\\'


class MainHandler(tornado.web.RequestHandler, ABC):
    def get(self):
        self.render('index.html')


class ReceiveHandler(tornado.web.RequestHandler, ABC):

    def post(self):
        file_name = None
        post_data = self.request.body_arguments
        # print(post_data.keys())
        key = post_data.get('key')[0].decode("utf-8")
        # checkId = post_data.get('checkId')[0].decode("utf-8") 
        if key == "znst20210505":
            if 'zip_file' in self.request.files:  # 提交了zip文件
                checkId = int(time.time()) % 1000000  # unique id for this task
                file_metas = self.request.files["zip_file"]
                print("Upload zip file for {:d}".format(checkId))
                file_dir = os.path.join("results", str(checkId))
                for meta in file_metas:
                    file_name = meta['filename']
                    if not os.path.exists(file_dir):
                        os.makedirs(file_dir)
                    file_name = os.path.join(file_dir, file_name)

                    with open(file_name, 'wb') as up:
                        up.write(meta['body'])

                return_data = json.dumps({"code": 200, "msg": "正常返回", "data": {"checkId": checkId}}, ensure_ascii=False)
                print(return_data)
                self.finish(return_data)

                if zipfile.is_zipfile(file_name):  # 检查是否为zip文件
                    with zipfile.ZipFile(file_name, 'r') as zipf:
                        zipf.extractall(file_dir)

                    # 修改计算书的名字,去掉中文乱码
                    for file in os.listdir(os.path.join(file_dir, 'calculations')):
                        file_path = os.path.join(file_dir, 'calculations', file)
                        os.rename(file_path, file_path.encode('cp437').decode('gbk'))

                print("Start rules checking")
                report = main_check(file_dir, checkId)
                with open(os.path.join(file_dir, str(checkId) + '.json'), 'w') as f:
                    json.dump(report, f, ensure_ascii=False, indent=4)
                print("End rules checking")
            else:  # 没有提交zip 文件
                return_data = json.dumps({"code": 208, "msg": "没有上传zip文件", "data": {"checkId": ""}}, ensure_ascii=False)
                print(return_data)
                self.finish(return_data)
        else:
            return_data = json.dumps({"code": 205, "msg": "密码错误"}, ensure_ascii=False)
            print(return_data)
            self.finish(return_data)


settings = {
    'template_path': 'template',
}

application = tornado.web.Application([
    # (r"/", MainHandler),
    (r"/", ReceiveHandler),
], **settings)

if __name__ == "__main__":
    application.listen(8010)
    tornado.ioloop.IOLoop.instance().start()
