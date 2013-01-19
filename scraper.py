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

singer_song_map = {}

def urlify (name):
    return name.replace(' ', '+')

def process_singer(name, level): 

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

    artist_search = spotify.artists.search(name)
    try:
        curr_artist = artist_search.next()
    except:
        curr_artist = None
        return None

    popularity = 0
    if curr_artist:
        popularity = float(curr_artist.popularity)

    song_search = spotify.tracks.search(name)

    try:
        curr_song = song_search.next()
    except:
        curr_song = None
        return None

    song = ""
    stream_id = 0
    song_pop = 0
    song_cover_url = ""

    if curr_song:
        song = curr_song.name
        song_pop = float(curr_song.popularity)

        gs_search = gc.search(str(song) + " " + str(name))
        
        try:
            gs_song = gs_search.next() 
            stream_id = int(gs_song.id)
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
    item['song_id'] = stream_id
    item['song_cover'] = song_cover_url
    singer_song_map[name] = (song, song_pop, stream_id, song_cover_url) 

    item['peer_song_name'] = []
    item['peer_song_pop'] = []
    item['peer_song_id'] = []
    item['peer_song_cover'] = []

    print 'Added singer %s to database' % item['name']

    #return early because there's no point in recursing through 
    new_peers = list(peers)

    #Go a level down 
    for peer in peers:
        if peer not in singer_song_map.keys():
            peer_song_data = process_singer(peer, level-1)

            if not peer_song_data:
                new_peers.remove(peer)
                continue

            #store info on our peer
            item['peer_song_name'].append(peer_song_data[0])
            item['peer_song_pop'].append(peer_song_data[1])
            item['peer_song_id'].append(peer_song_data[2])
            item['peer_song_cover'].append(peer_song_data[3])

            singer_song_map[peer] = peer_song_data

        #peer's already there, let's look up and get the statistics in a global structure we've saved
        #only using global structure to save mongo queries
        else:
            peer_song_data = singer_song_map[peer]
            item['peer_song_name'].append(peer_song_data[0])
            item['peer_song_pop'].append(peer_song_data[1])
            item['peer_song_id'].append(peer_song_data[2])
            item['peer_song_cover'].append(peer_song_data[3])

    item['peers'] = new_peers
    singer_coll.update({'_id': _id}, item, upsert=True)
    return (song, song_pop, stream_id, song_cover_url)


def add_singers(singers):

    for singer in singers:
        process_singer(singer, 1)

if __name__ == '__main__':
    singers = ['The Rolling Stones']
    add_singers(singers)

