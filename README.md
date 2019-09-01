# KEXP -> SPOTIFY 

## Spotify Setup
Visit https://developer.spotify.com/dashboard/applications to create a clientid.

Be sure to white-list a redirect URI (Eg https://localhost:8080)

The redirect URI doesn't have to be functional but you will need to copy it from your browser when prompted.

I manually created an empty playlist in Spotify called "KEXP Weekly". It can also be done programmatically but this was most straightforward.

## Methodology
Daily KEXP playlists are cached to avoid over-querying. We're hitting the endpoint that serves the main kexp.org web page.  BE POLITE!

We count up total plays by artist and choose the top 25.  Nothing special is done to manage ties.  For each song by the artist that was played we first do an 'artist:','track:' search for an exact match, and if nothing comes up we fall back to keyword search by artist and track.

We also add a special bonus track at the end, just for the lols.

## Prerequisites:
````
pip install spotipy
````

I made some minor revisions to my spotipy installation to bring it up to date.  You may have to troubleshoot calls to the module to get things working.  Reach out to me if you get stuck.
