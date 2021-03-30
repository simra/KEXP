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
import argparse

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
                    try:
                        result.raise_for_status()
                    except requests.exceptions.HTTPError as err:
                        print(err)
                        sys.exit(1)
                    #print(json.dumps(result))
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
    

def plotArtistTrack(config, catalog):
    all_results={}

    pivots = ['artist','track']
    # we rank artists by most plays, take the top 25 and 
    # add their played tracks to the playlist.
    #pivot = config['pivot'] if 'pivot' in config else 'artist'
    for pivot in pivots:
        result = {}
        print(f'Grouping by {pivot}')
        for r in catalog:
            if r['track'] is None:
                continue
            artistid = r[pivot]['name']
            if pivot == 'track':
                artistid += ';;'+r['artist']['name']
            if artistid not in result:
                result[artistid]={'track':r, 'plays':set(), 'songs':set()}
            result[artistid]['plays'].add(r['airdate']) # count by unique timestamps. Sometimes the playlist has duplicates.
            result[artistid]['songs'].add((r['artist']['name'],r['track']['name']))
        all_results[pivot]=result
        
    from collections import Counter
    ctr = {}
    for t in all_results['track']:
        (track,_,artist) = t.split(';')
        track_plays = len(all_results['track'][t]['plays'])
        artist_plays = len(all_results['artist'][artist]['plays'])
        #print(t,track_plays, artist_plays)
        key = (track_plays, artist_plays)
        if key not in ctr:
            ctr[key]=set()
        ctr[key].add(t)
    
    import matplotlib.pyplot as plt
    import mpld3
    from math import log, ceil

    data = [(x,y,ctr[(x,y)]) for (x,y) in ctr]
    x_track=[d[0] for d in data]
    y_artist=[d[1] for d in data]
    count = [len(d[2]) for d in data]
    labels = [','.join(d[2]) for d in data]
    
    fig, ax = plt.subplots(figsize=(4,2)) #subplot_kw=dict(axisbg='#EEEEEE'))
    scatter = ax.scatter(x_track, y_artist, s=[3*log(c+1) for c in count])
    xint = range(min(x_track), ceil(max(x_track))+1)
    #ax.set_xticks(xint)
    ax.set_xlabel('Track Plays')
    ax.set_ylabel('Artist Plays')
    tooltip = mpld3.plugins.PointLabelTooltip(scatter, labels=labels)
    mpld3.plugins.connect(fig, tooltip)
    mpld3.show()
    #plt.show()
    #print(ctr)

def plotTop40(config, catalog):
    from datetime import datetime
    from epiweeks import Week
    
    pivot = 'artist'
    # we rank artists by most plays, take the top 25 and 
    # add their played tracks to the playlist.
    #pivot = config['pivot'] if 'pivot' in config else 'artist'

    result = {}
    print(f'Grouping by {pivot}')
    for r in catalog:
        if r['track'] is None:
            continue
        artistid = r[pivot]['name']
        if pivot == 'track':
            artistid += ';;'+r['artist']['name']
        week = Week.fromdate(datetime.strptime(r['airdate'], '%Y-%m-%dT%H:%M:%SZ'))
        if week not in result:
            result[week]={}
        if artistid not in result[week]:
            result[week][artistid]={'track':r, 'plays':set(), 'songs':set()}
        
        result[week][artistid]['plays'].add(r['airdate']) # count by unique timestamps. Sometimes the playlist has duplicates.
        result[week][artistid]['songs'].add((r['artist']['name'],r['track']['name']))
    print([w for w in result])
    
    all_results = result
    if 0:
        all_artists = []
        plots = {}
        N=10
        W=20
        weeks = list(sorted(all_results))[-W:]
        for w in weeks:
            result = all_results[w]
            topN = list(sorted(result, key=lambda x: len(result[x]['plays']), reverse=True))[:N]
            print(topN)
            for i,a in enumerate(topN):
                if a not in all_artists:
                    all_artists.append(a)
                if a not in plots:
                    plots[a]=[]
                plots[a].append((w,i))
            #ranks.append(topN)
        y0_values = dict((k,N-v+1) for v,k in enumerate(all_artists))
        x_values = dict([(k,v+1) for (v,k) in enumerate(weeks)])
        import matplotlib.pyplot as plt
        from math import isnan
        fig, ax = plt.subplots(figsize=(12,8)) #subplot_kw=dict(axisbg='#EEEEEE'))
        for a in plots:
            lookup = dict(plots[a])
            X = [x_values[w] for w in weeks] #[x_values[w] for (w,_) in plots[a]]
            Y = [N-lookup[w] if w in lookup else float('NaN') for w in weeks] #N-v for (_,v) in plots[a]]
            ax.plot(X, Y, 'o-')
            for i in range(len(X)):
                if i==0 or (not isnan(Y[i]) and isnan(Y[i-1])):
                    ax.text(X[i],Y[i]+0.15, a, ha='center', fontsize=8)
            ax.set_yticks(range(N+1))
            ax.set_yticklabels(['']+[str(N-y) for y in range(N)])
        plt.show()

    threshold = Week.fromdate(datetime(2020,5,26))
    summary = {}
    from collections import Counter
    denom = Counter()
    for w in all_results:
        isprior = w<threshold
        denom[isprior]+=1
        current = all_results[w]
        for a in current:
            if a not in summary:
                summary[a]=Counter()
            summary[a][isprior]+=len(current[a]['plays'])
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12,8)) 
    labels = []
    N=20
    for i,a in enumerate(list(sorted(summary, key = lambda x: summary[x][True]+summary[x][False]))[-N:]):
        ax.plot([2*i-0.5,2*i+0.5], [summary[a][True]/denom[True], summary[a][False]/denom[False]],'o-')
        labels.append(a)
        print('{}\t{}\t{}'.format(a, summary[a][True]/denom[True], summary[a][False]/denom[False]))
    ax.set_xticks([2*i for i in range(N)])
    ax.set_xticklabels(labels, rotation=90)
    ax.set_ylabel('Plays per Week')
    plt.tight_layout()
    plt.savefig('playsPerWeek.png')
    plt.show()

    if 0:
        import mpld3
        from math import log, ceil

        data = [(x,y,ctr[(x,y)]) for (x,y) in ctr]
        x_track=[d[0] for d in data]
        y_artist=[d[1] for d in data]
        count = [len(d[2]) for d in data]
        labels = [','.join(d[2]) for d in data]
        
        fig, ax = plt.subplots(figsize=(4,2)) #subplot_kw=dict(axisbg='#EEEEEE'))
        scatter = ax.scatter(x_track, y_artist, s=[3*log(c+1) for c in count])
        xint = range(min(x_track), ceil(max(x_track))+1)
        #ax.set_xticks(xint)
        ax.set_xlabel('Track Plays')
        ax.set_ylabel('Artist Plays')
        tooltip = mpld3.plugins.PointLabelTooltip(scatter, labels=labels)
        mpld3.plugins.connect(fig, tooltip)
        mpld3.show()
        #plt.show()
        #print(ctr)



def parseArgs():
    parser = argparse.ArgumentParser('Process KEXP playlist and upload to spotify')
    parser.add_argument('--config', type=str, default='config.json', help='Config file in json format')
    return parser.parse_args()

def main():
    args=parseArgs()
    with open(args.config, 'r', encoding='utf-8') as inCfg:
        config=json.load(inCfg)
    
    setEnvironment(config)
    catalog=collectFromKEXP(config)
    plotTop40(config, catalog)

if __name__ == "__main__":
    main()