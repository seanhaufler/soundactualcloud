import urllib2
import pymongo 
import md5
import grooveshark
import facepy
import wikipedia
import google
import soundcloud

#from spotify_api.api import SpotifyApi
from bs4 import BeautifulSoup

mongo_conn = pymongo.Connection('localhost:27017')
singer_coll = mongo_conn['artists']['singer']

fb_graph = facepy.GraphAPI()
sc_client = soundcloud.Client(client_id='15796297f59f225886f6247ba56a1a43')

#spotify = SpotifyApi()
gc = grooveshark.Client()
gc.init()

singer_song_map = {}
eval_lst = ['Pink']

def urlify (name):
    return name.replace(' ', '+')

def get_stats(name):
    name = name.encode('ascii', 'ignore')

    soup = ""
    try: 
        soup = BeautifulSoup(urllib2.urlopen('http://www.music-map.com/' + urlify(name) + '.html').read())
    except:
        return None

    a_tags = soup.find_all('a')
    peers = []

    # Add all the peers to our peers table
    for entry in a_tags:
        if entry.get('class') == ['S']:
            if entry.string != name:
                peers.append(entry.string)

    try:
        song_search = gc.search(name)
        song_result = song_search.next()
    except:
        return None

    #Get an image for the name 
    try:
        google_search = google.Google.search_images(name)
        result = google_search[0]
        song_cover_url = result.link
    except:
        song_cover_url = "http://www.google.com/"

    #get song name, id, and popularity
    song = song_result.name
    stream_id = int(song_result.id)
    song_pop = song_result.popularity

    #get facebook page for the group 
    fb_search = fb_graph.search(name, 'page')
    fb_page = "http://www.facebook.com"

    if 'data' in fb_search:
        if fb_search['data'] and 'id' in fb_search['data'][0]:
            fb_page = "http://www.facebook.com/" + str(fb_search['data'][0]['id'])

    try:
        desc = wikipedia.getArticle(name)
    except:
        desc = name

    wiki_url = "http://en.wikipedia.org/w/index.php?title=%s" % name.replace(' ', '_')
    sc_url = "http://soundcloud.com"

    try:
        sc_result = sc_client.get('/tracks', key=(song.encode('ascii', 'ignore') + " " + name.encode('ascii', 'ignore'))) 
        sc_url = sc_result[0].permalink_url 
    except:
        sc_url = "http://soundcloud.com"
        
    item = {}
    _id = md5.md5(name).hexdigest() 
    item['_id'] = _id 
    item['name'] = name
    item['desc'] = desc
    item['wiki_url'] = wiki_url
    item['sc_url'] = sc_url
    item['fb_page'] = fb_page
    item['song'] = song
    item['song_pop'] = song_pop
    item['song_id'] = stream_id
    item['song_cover'] = song_cover_url
    item['peers'] = {}

    singer_song_map[name] = item
    return (item, peers)

def process_singer(name): 

    cursor = singer_coll.find({'name':name})

    #already in there, fuck it
    if cursor.count() > 0:
        print 'Skipping %s, already in there' % name
        return

    try:
        item,peers = get_stats(name)
    except TypeError,ValueError:
        return

    for peer in peers:
        if peer not in singer_song_map:
            eval_lst.append(peer)
            try:
                it, pr = get_stats(peer)
                item['peers'][peer] = it 
            except TypeError,ValueError:
                pass

        else:
            peer_data = singer_song_map[peer]
            item['peers'][peer] = peer_data

    try:
        singer_coll.update({'_id': _id}, item, upsert=True)
        print 'Inserting %s' % item['name']
    except:
        return

def add_singers():

    while len(eval_lst) > 0:
        singer = eval_lst.pop(0)
        process_singer(singer)

if __name__ == '__main__':
    add_singers()

