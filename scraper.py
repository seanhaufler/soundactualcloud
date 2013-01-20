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

def urlify (name):
    return name.replace(' ', '+')

def process_singer(name, level): 

    if name in singer_song_map:
        return singer_sing_map[name]

    #We've gone 5 levels done, just keep going 
    if level < 0:
        return None

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

    song_search = gc.search(name)

    try:
        song_result = song_search.next()
    except:
        return None

    #Get an image for the name 
    google_search = google.Google.search_images(name)
    result = google_search[0]
    song_cover_url = result.link

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

    desc = wikipedia.getArticle(name)
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
    singer_song_map[name] = item 

    item['peers'] = {}

    print 'Added singer %s to database' % item['name']
    print 'Image URL is %s' % item['song_cover']
    try:
        singer_coll.update({'_id': _id}, item, upsert=True)
    except:
        pass

    #Go a level down 
    for peer in peers:
        if peer not in singer_song_map:
            peer_data = process_singer(peer, level-1)

            if not peer_data:
                continue

            peer_data['peers'] = {}
            
            item['peers'][peer] = peer_data 
            singer_song_map[peer] = peer_data

        #peer's already there, let's look up and get the statistics in a global structure we've saved
        #only using global structure to save mongo queries
        else:
            peer_data = singer_song_map[peer]
            peer_data['peers'] = {}
            item['peers'][peer] = peer_data

    cursor = singer_coll.find({'_id':_id})
    doc = cursor.next()

    if len(doc['peers']) <= len (item['peers']):
        try:
            singer_coll.update({'_id': _id}, item, upsert=True)
        except:
            pass

    return item 

def add_singers(singers):

    for singer in singers:
        process_singer(singer, 1)

if __name__ == '__main__':
    singers = ['The Rolling Stones']
    add_singers(singers)

