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
names_coll = mongo_conn['artists']['names']

class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/map", MapHandler),
            (r"/render", SearchHandler),
            (r"/related", ApiHandler),
            (r"/autocomplete", AutocompleteHandler),
            ]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class BaseHandler(tornado.web.RequestHandler):
    pass

class AutocompleteHandler(BaseHandler):
    def get(self):
        global names_coll 
        names = names_coll.find()
        names_lst = []
        for entry in names:
            names_lst.append(str(entry['_id']))
        lower_case_names = map(str.lower, names_lst)
        term = self.get_argument('term', "")

        result = []
        for index, name in enumerate(lower_case_names):
            if term.lower() in name:
                result.append(names_lst[index])

        print result

        self.write(json.dumps(result))


class HomeHandler(BaseHandler):
    def get(self):
        self.render("index.html")

class TestHandler(BaseHandler):
    def get(self):
        self.render("test.html")

class MapHandler(BaseHandler):
    def get(self):
        artist = self.get_argument('artist')
        self.render("map.html", artist=artist)


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

