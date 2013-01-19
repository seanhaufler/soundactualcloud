# Python
import os
import json
import random
import urllib
import urllib2
import re
import textwrap
import heapq

# Tornado
import tornado.httpserver
import tornado.httpclient
import tornado.options
import tornado.ioloop
import tornado.web

# Mongo
import pymongo
from bson import json_util

#FSQOauthToken = "QYEIVBMULP11CPVHP4MSHXDB2VIZ12LDDUTMMJL2YSP2IJJA"
#FSQOauthSecret = "L04TIELKXWIHKVXWI1PRENGM1YFSPHHX0PEUZQSUIMDVHDDU"

#FB
#import fbconsole

class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    pass

class HomeHandler(BaseHandler):
    def get(self):
        self.render("index.html")

def main(port='3000', address='127.0.0.1'):
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(port, address)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()

