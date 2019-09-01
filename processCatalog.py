import json

import pprint
import sys
import os
import subprocess

import spotipy
import spotipy.util as util
import datetime
import time
import requests

# Sample config:
# Visit https://developer.spotify.com/dashboard/applications to create a clientid.
# Be sure to white-list a redirect URI (Eg https://localhost:8080)
# The redirect URI doesn't have to be functional but you will need to copy it 
# from your browser when prompted.
# {
#    'environment': {
#       'SPOTIPY_CLIENT_ID': <your spotify app id>,
#       'SPOTIPY_CLIENT_SECRET': <the secret for your spotify app id>
#       'SPOTIPY_REDIRECT_URI': 'https://localhost:8080'
#    },
#
# }    

def setEnvironment(config):
    if 'environment' in config:
        for e in config['environment']:
            os.environ[e]=config['environment'][e]

def formatDate(date):
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")

def makeUrl(startdate, enddate):
    print(startdate,enddate)
    return '{}/play?begin_time={}&end_time={}&ordering=airdate'.format(
        'https://legacy-api.kexp.org',
        formatDate(startdate), formatDate(enddate))

def fetchDate(start, end):
    # TODO: this is currently only capturing the first 100 tracks of the day.
    cacheFn = 'cache/{}.json'.format(start.strftime("%Y%m%d"))
    print("Fetching {}".format(start.strftime("%Y-%m-%d")))                        
    
    if not os.path.exists(cacheFn): 
        cachetracks=[]
        while (start<end):       
            nextUrl = makeUrl(start, start+datetime.timedelta(hours=1))
            while nextUrl is not None:
                print('\t'+nextUrl.replace('https://legacy-api.kexp.org',''))
                result=requests.get(nextUrl)
                if result.ok:
                    response = result.json()
                    tracks = response['results']
                    nextUrl = response['next'] if len(tracks)>0 else None
                    print(len(tracks))
                    for t in tracks:
                        #print(json.dumps(t))
                        if 'track' in t:
                            cachetracks.append(t)
                            #print(t['airdate'])
                else:
                    print(json.dumps(result))
                    nextUrl=None
            start=start+datetime.timedelta(hours=1)
            time.sleep(1)
            #print(formatDate(start))
            #exit()

        with open(cacheFn,'w', encoding='utf-8') as outCache:
            outCache.write(json.dumps(cachetracks))
    tracks=[]
    print("Loading {}".format(cacheFn))
    with open(cacheFn, 'r', encoding='utf-8') as inCache:
        tracks = json.load(inCache)
    print(len(tracks))
    return tracks



def collectFromKEXP(config):
    daysToParse= config['daysToParse'] if 'daysToParse' in config else 7

    today = datetime.datetime.fromordinal(datetime.datetime.utcnow().date().toordinal())
    start_date = today - datetime.timedelta(days=daysToParse)
    end_date = start_date + datetime.timedelta(days=1)
    results = []
    while (start_date<today):
        results += fetchDate(start_date,end_date)
        start_date = start_date + datetime.timedelta(days=1)
        end_date = start_date + datetime.timedelta(days=1)
    print("All results: ",len(results))
    return results  
    

def updateSpotify(config, catalog):
    result={}

    # we rank artists by most plays, take the top 25 and 
    # add their played tracks to the playlist.
    for r in catalog:
        if r['track'] is None:
            continue
        artistid = r['artist']['name']
        if artistid not in result:
            result[artistid]={'track':r, 'plays':set(), 'songs':set()}
        result[artistid]['plays'].add(r['airdate']) # count by unique timestamps. Sometimes the playlist has duplicates.
        result[artistid]['songs'].add(r['track']['name'])
    
    print(len(result['Portishead']['plays']))
    username = config['spotify_username']
    playlist_name= config['playlist_name']
    
    # If you don't have a cached token this will trigger a web flow.
    scope = 'playlist-modify-public playlist-modify-private'
    token = util.prompt_for_user_token(username, scope)

    if token:
        sp = spotipy.Spotify(auth=token)
        #sp.trace = True
        #sp.trace_out = True
        #print(dir(sp))
        # It's better to create this manually.
        #playlists = sp.user_playlist_create(username, playlist_name, description=playlist_description, public=True)
        #                                    #playlist_description)    
        #pprint.pprint(playlists)
        playlists=sp.user_playlists(username)
        
        pl_id=None
        for r in playlists['items']:            
            if r['name']==playlist_name:
                pl_id=r['id']
        if pl_id is None:
            raise Exception("Can't find playlist {}".format(config['playlist_name']))

        track_ids = []
        for r in sorted(result, key=lambda x: len(result[x]['plays']), reverse=True)[0:25]:
            print(r,len(result[r]['plays']))
            for s in result[r]['songs']:
                print('\t{}'.format(s))            
                query = "artist:{} track:{}".format(r,s)
                try:
                    searchResult=sp.search(query)
                    if (len(searchResult['tracks']['items'])>0):
                        #pprint.pprint(searchResult['tracks']['items'][0])
                        track_ids.append(searchResult['tracks']['items'][0]['id'])
                    else:
                        print("No search result for {}".format(query))
                        # try a keyword search instead
                        query= "{} {}".format(r,s)
                        searchResult=sp.search(query)
                        if (len(searchResult['tracks']['items'])>0):
                            track_ids.append(searchResult['tracks']['items'][0]['id'])
                        else:
                            print("No fallback result either.")
                except:
                    print("Failed: {}".format(query))    
        
        print('Pushing {} tracks'.format(len(track_ids)))

        sp.user_playlist_replace_tracks(username, pl_id, track_ids[0:100])
        if len(track_ids)>100:
            sp.user_playlist_add_tracks(username, pl_id, track_ids[100:])
        playlist_description ='Top 25 artists on KEXP, {} days ending {}'.format(config['daysToParse'], datetime.datetime.utcnow().strftime('%x'))
        sp.user_playlist_change_details(username, pl_id, description= playlist_description)
    else:
        print("Can't get token for", username)

def main():
    with open('config.json', 'r', encoding='utf-8') as inCfg:
        config=json.load(inCfg)
    
    setEnvironment(config)
    catalog=collectFromKEXP(config)
    updateSpotify(config, catalog)

if __name__ == "__main__":
    main()