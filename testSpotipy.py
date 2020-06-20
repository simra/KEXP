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
import re

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

def testSpotify(config):
    result={}

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
        print('Found pl_id: {}'.format(pl_id))

    else:
        print("Can't get token for", username)

def main():
    with open('config.json', 'r', encoding='utf-8') as inCfg:
        config=json.load(inCfg)
    
    setEnvironment(config)
    testSpotify(config)

if __name__ == "__main__":
    main()