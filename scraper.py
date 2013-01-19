import urllib2
import pymongo 
import md5
import grooveshark

from spotify_api.api import SpotifyApi
from bs4 import BeautifulSoup

mongo_conn = pymongo.Connection('localhost:27017')
singer_coll = mongo_conn['artists']['singer']

#sc_client = soundcloud.Client(client_id='15796297f59f225886f6247ba56a1a43')

spotify = SpotifyApi()
gc = grooveshark.Client()
gc.init()

#tw = twitter.Twitter(auth=twitter.OAuth('406096834-dqtFJQ0jAieZ9YrvJmEE2nByxMtFwXYsMmdRUhwG',
#                                        'uHG8KiEGWNbT2laOlN3BhDwCaVi45PBtTp29JdmO3O8',
#                                        'reNWgFX6HsWWDLXVvOYt6A',
#                                        'V2YuSIxTNKc99z7upSQvFCWKUMhSi6A56Y76WJjo')) 

singers_added = []

def urlify (name):
    return name.replace(' ', '+')

def process_singer(name, level): 

    #We've gone 5 levels done, just keep going 
    if level == 0:
        return

    soup = BeautifulSoup(urllib2.urlopen('http://www.music-map.com/' + urlify(name) + '.html').read())
    a_tags = soup.find_all('a')
    peers = []

    # Add all the peers to our peers table
    for entry in a_tags:
        if entry.get('class') == ['S']:
            if entry.string != name:
                peers.append(entry.string)

    artist_search = spotify.artists.search(name)
    try:
        curr_artist = artist_search.next()
    except StopIteration:
        curr_artist = None

    popularity = 0
    if curr_artist:
        popularity = float(curr_artist.popularity)

    song_search = spotify.tracks.search(name)

    try:
        curr_song = song_search.next()
    except StopIteration:
        curr_song = None

    song = ""
    stream_url = ""
    song_pop = 0
    song_cover_url = ""

    if curr_song:
        song = curr_song.name
        song_pop = float(curr_song.popularity)

        #search grooveshark code here
        gs_search = gc.search(song + " " + name)
        
        try:
            gs_song = gs_search.next() 
            stream_url = gs_song.stream.url
            song_cover_url = gs_song.export()['cover']
        except:
            pass


    item = {}
    _id = md5.md5(name).hexdigest() 
    item['_id'] = _id 
    item['name'] = name
    item['peers'] = peers
    item['pop'] = popularity 
    item['song'] = song
    item['song_pop'] = song_pop
    item['song_url'] = stream_url
    singer_coll.update({'_id': _id}, item, upsert=True)
    singers_added.append(name)
    print 'Added singer %s to database' % item['name']

    #Go a level down 
    for peer in peers:
        if peer not in singers_added:
            singers_added.append(peer)
            process_singer(peer, level-1)
            break


def add_singers(singers):

    for singer in singers:
        process_singer(singer, 4)

if __name__ == '__main__':
    singers = ['The Rolling Stones']
    add_singers(singers)

