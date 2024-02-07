import json
import sys
import os
import spotipy
import spotipy.util as util
import datetime
import time
import requests
import re
import argparse

# Sample config:
# Visit https://developer.spotify.com/dashboard/applications to create a
# clientid. Be sure to white-list a redirect URI (Eg https://localhost:8080)
# The redirect URI doesn't have to be functional but you will need to copy
#  it from your browser when prompted.
# {
#    'environment': {
#       'SPOTIPY_CLIENT_ID': <your spotify app id>,
#       'SPOTIPY_CLIENT_SECRET': <the secret for your spotify app id>
#       'SPOTIPY_REDIRECT_URI': 'https://localhost:8080'
#    },
#
# }

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)

def setEnvironment(config):
    if 'environment' in config:
        for e in config['environment']:
            os.environ[e] = config['environment'][e]


def formatDate(date):
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")


def makeUrl(startdate, enddate):
    uprint(startdate, enddate)
    return '{}/play?begin_time={}&end_time={}&ordering=airdate'.format(
        'https://legacy-api.kexp.org',
        formatDate(startdate), formatDate(enddate))


def fetchDate(start, end):
    # TODO: this is currently only capturing the first 100 tracks of the day.
    cacheFn = 'cache/{}.json'.format(start.strftime("%Y%m%d"))
    uprint("Fetching {}".format(start.strftime("%Y-%m-%d")))

    if not os.path.exists(cacheFn):
        cachetracks = []
        while (start < end):
            nextUrl = makeUrl(start, start+datetime.timedelta(hours=1))
            while nextUrl is not None:
                uprint('\t'+nextUrl.replace('https://legacy-api.kexp.org', ''))
                result = requests.get(nextUrl)
                if result.ok:
                    response = result.json()
                    tracks = response['results']
                    nextUrl = response['next'] if len(tracks) > 0 else None
                    uprint(len(tracks))
                    for t in tracks:
                        # print(json.dumps(t))
                        if 'track' in t:
                            cachetracks.append(t)
                            # print(t['airdate'])
                else:
                    try:
                        result.raise_for_status()
                    except requests.exceptions.HTTPError as err:
                        uprint(err)
                        sys.exit(1)
                    # print(json.dumps(result))
                    nextUrl = None
            start = start + datetime.timedelta(hours=1)
            time.sleep(1)
            # print(formatDate(start))
            # exit()

        with open(cacheFn, 'w', encoding='utf-8') as outCache:
            outCache.write(json.dumps(cachetracks))
    tracks = []
    uprint("Loading {}".format(cacheFn))
    with open(cacheFn, 'r', encoding='utf-8') as inCache:
        tracks = json.load(inCache)
    uprint(len(tracks))
    return tracks


def collectFromKEXP(config):
    daysToParse = config['daysToParse'] if 'daysToParse' in config else 7

    today = datetime.datetime.fromordinal(
        datetime.datetime.utcnow().date().toordinal())
    start_date = today - datetime.timedelta(days=daysToParse)
    end_date = start_date + datetime.timedelta(days=1)
    results = []
    while (start_date < today):
        results += fetchDate(start_date, end_date)
        start_date = start_date + datetime.timedelta(days=1)
        end_date = start_date + datetime.timedelta(days=1)
    uprint("All results: ", len(results))
    return results


def updateSpotify(config, catalog):
    result = {}

    # we rank artists by most plays, take the top 25 and
    # add their played tracks to the playlist.
    pivot = config['pivot'] if 'pivot' in config else 'artist'
    uprint(f'Grouping by {pivot}')
    for r in catalog:
        if r['track'] is None or r['artist'] is None:
            continue
        artistid = r[pivot]['name']
        if pivot == 'track':
            artistid += '; '+r['artist']['name']
        if artistid not in result:
            result[artistid] = {'track': r, 'plays': set(), 'songs': set()}
        # count by unique timestamps. Sometimes the playlist has duplicates.
        result[artistid]['plays'].add(r['airdate'])
        result[artistid]['songs'].add(
            (r['artist']['name'], r['track']['name']))

    username = config['spotify_username']
    playlist_name = config['playlist_name']

    # If you don't have a cached token this will trigger a web flow.
    scope = 'playlist-modify-public playlist-modify-private'
    token = util.prompt_for_user_token(username, scope)

    if token:
        sp = spotipy.Spotify(auth=token)
        playlists = sp.user_playlists(username)
        pl_id = None
        for r in playlists['items']:
            if r['name'] == playlist_name:
                pl_id = r['id']
        if pl_id is None:
            raise Exception("Can't find playlist {}".format(
                config['playlist_name']))

        track_ids = []
        topN = config['topN'] if 'topN' in config else 25
        for r in sorted(result, key=lambda x: len(result[x]['plays']),
                        reverse=True)[0:topN]:
            uprint(r, len(result[r]['plays']))
            for a, s in result[r]['songs']:
                uprint('\t{}'.format(s))
                s = re.sub(r'\(feat. .*\)', '', s).strip()
                query = "artist:{} track:{}".format(a, s)
                try:
                    searchResult = sp.search(query)
                    if len(searchResult['tracks']['items']) > 0:
                        track = searchResult['tracks']['items'][0]['id']
                        if track not in track_ids:
                            # pprint.pprint(searchResult['tracks']['items'][0])
                            track_ids.append(track)
                        else:
                            uprint("\tskipping duplicate item for {}".format(
                                query))
                    else:
                        uprint("\tNo search result for {}".format(query))
                        # try a keyword search instead
                        a_scrub = a
                        if 'feat.' in a_scrub.lower():
                            a_scrub = a_scrub[:a_scrub.lower().index('feat.')]
                        a_scrub = a_scrub.replace('&', '')
                        s_scrub = s.replace('&', '')
                        query = "{} {}".format(a_scrub, s_scrub)
                        searchResult = sp.search(query)
                        if (len(searchResult['tracks']['items']) > 0):
                            track = searchResult['tracks']['items'][0]
                            if track['id'] not in track_ids:
                                uprint('\tFound track: {} ; {}'.format(
                                    track['artists'][0]['name'], track['name'])
                                    )
                                track_ids.append(track['id'])
                            else:
                                uprint("\tskipping duplicate item for {}".
                                      format(query))
                        else:
                            uprint("\t** No fallback result either.")
                except Exception as e:
                    uprint("Failed: {}\n{}".format(query, e))

        # Add a bonus track. ;-)
        bonus = "1yYzqYzzXtAKxtUIIXmYgp"
        if bonus not in track_ids:
            track_ids.append(bonus)
        uprint('Pushing {} tracks'.format(len(track_ids)))

        sp.user_playlist_replace_tracks(username, pl_id, track_ids[0:100])
        track_ids = track_ids[100:]

        while len(track_ids) > 0:
            sp.user_playlist_add_tracks(username, pl_id, track_ids[0:100])
            track_ids = track_ids[100:]

        playlist_description = 'Top tracks on KEXP, {} days ending {}. ' \
            'Become an Amplifier at KEXP.org'. \
            format(config['daysToParse'],
                   datetime.datetime.utcnow().strftime('%x'))
        sp.user_playlist_change_details(username, pl_id,
                                        description=playlist_description)
    else:
        uprint("Can't get token for", username)


def parseArgs():
    parser = argparse.ArgumentParser(
        'Process KEXP playlist and upload to spotify')
    parser.add_argument('--config', type=str, default='config.json',
                        help='Config file in json format')
    return parser.parse_args()


def main():
    args = parseArgs()
    with open(args.config, 'r', encoding='utf-8') as inCfg:
        config = json.load(inCfg)

    setEnvironment(config)
    catalog = collectFromKEXP(config)
    updateSpotify(config, catalog)


if __name__ == "__main__":
    main()
