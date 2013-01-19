# Python
import os
import json
import random
import urllib
import urllib2
import md5
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

mongo_conn = pymongo.Connection('localhost:27017')
singer_coll = mongo_conn['artists']['singer']

class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/render", SearchHandler),
            (r"/related", ApiHandler)
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

class SearchHandler(BaseHandler):
    def post(self):
        artist = self.get_argument('artist')
        search_hash = md5.md5(artist).hexdigest()
        search_results = singer_coll.find({'_id':search_hash})

        #must be one
        if search_results.count() > 0:
            result = search_results[0]
            
            self.render('search.html', name=result['name'], song=result['song'], 
                    url=result['song_id'], peers=result['peers'], peer_songs=result['peer_song_name'],
                    peer_song_ids=result['peer_song_id'])
        else:
            self.render('error.html')

class ApiHandler(BaseHandler):
    def get(self):
        artist = self.get_argument('artist')
        search_hash = md5.md5(artist).hexdigest()
        search_results = singer_coll.find({'_id':search_hash})

        #must be one
        if search_results.count() > 0:
            result = search_results[0]
            self.write(json.dumps(result))
        else:
            self.write("{}")

def main(port='3000', address='127.0.0.1'):
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(port, address)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()

