#!/usr/bin/env python
# -*- coding:utf-8 -*-
from abc import ABC

import tornado.ioloop
import tornado.web
import os
import json

os.path.altsep = '\\'


class MainHandler(tornado.web.RequestHandler, ABC):
    def get(self):
        self.render('index.html')


class ReceiveHandler(tornado.web.RequestHandler, ABC):

    def post(self):
        checkId = None
        post_data = self.request.body_arguments
        # print(post_data.keys())
        key = post_data.get('key')[0].decode("utf-8")
        # checkId = post_data.get('checkId')[0].decode("utf-8") 
        if key == "znst20210505":
            if 'checkId' in post_data.keys():
                checkId = post_data.get('checkId')[0].decode("utf-8")
                print("To obtain results for {:s}".format(checkId))
            if 'checkId' not in post_data.keys() or checkId == "":
                # 查询的信息没有checkId
                return_data = json.dumps({"code": 207, "msg": "无效checkId", "data": {"checkId": ""}}, ensure_ascii=False)
                print(return_data)
                self.finish(return_data)
            else:  # 有checkId, 读取判断结果
                # checkId is a string from direct get 
                path_dir = os.path.join(os.path.join('./results', checkId))
                if os.path.exists(path_dir):  # 存在上传的文件
                    if os.path.exists(os.path.join(path_dir, checkId + '.json')):  # 已经判断完成
                        with open(os.path.join(path_dir, checkId + '.json'), 'r') as f:
                            return_data = json.load(f)
                            return_data = json.dumps(return_data, ensure_ascii=False, indent=4)
                    else:  # 没有判断完成
                        return_data = json.dumps({"code": 206, "msg": "正在提取中", "data": {"checkId": int(checkId)}},
                                                 ensure_ascii=False)
                else:
                    return_data = json.dumps({"code": 207, "msg": "无效checkId", "data": {"checkId": int(checkId)}},
                                             ensure_ascii=False)

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
    application.listen(8011)
    tornado.ioloop.IOLoop.instance().start()
