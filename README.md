# KEXP -> SPOTIFY 

## Spotify Setup
Visit https://developer.spotify.com/dashboard/applications to create a clientid.

Be sure to white-list a redirect URI (Eg https://localhost:8080)

The redirect URI doesn't have to be functional but you will need to copy it from your browser when prompted.

Daily KEXP playlists are cached to avoid over-querying. We're hitting the endpoint that serves the main kexp.org web page.  BE POLITE!

## Prerequisites:
````
pip install spotipy
````

I made some minor revisions to my spotipy installation to bring it up to date.  You may have to troubleshoot calls to the module to get things working.  Reach out to me if you get stuck.
