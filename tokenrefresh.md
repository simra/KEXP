# Spotify Refresh Token Recovery

Use this when the weekly update workflow fails with an error like `invalid_grant` or `Refresh token expired`.

## What happened

The workflow seeds Spotipy's cache from the GitHub secret `SPOTIFY_REFRESH_TOKEN` and then calls Spotify to refresh the access token.

In this repository that happens in:

- `/home/runner/work/KEXP/KEXP/.github/workflows/weekly-catalog-update.yml`
- `/home/runner/work/KEXP/KEXP/processCatalog.py`

If the stored refresh token is expired, revoked, or otherwise invalid, the workflow cannot update the playlist until a new refresh token is generated and stored.

This does **not** by itself indicate a Spotify-wide API change. It usually means the saved token for this app/user pair is no longer valid.

## Generate a new refresh token locally

1. Create or confirm your Spotify app in the Spotify developer dashboard.
2. Make sure the app's redirect URI exactly matches the URI used by this repo, such as `https://localhost:8080`.
3. In the repository root, create a local config file from the sample:
   - Copy `/home/runner/work/KEXP/KEXP/config_sample.json` to `/home/runner/work/KEXP/KEXP/config.json`
4. Edit `/home/runner/work/KEXP/KEXP/config.json` and fill in:
   - `SPOTIPY_CLIENT_ID`
   - `SPOTIPY_CLIENT_SECRET`
   - `SPOTIPY_REDIRECT_URI`
   - `spotify_username`
   - `playlist_name`
5. Install the required package locally:
   - `pip install spotipy`
6. From the repository root, run:
   - `python /home/runner/work/KEXP/KEXP/testSpotipy.py`
7. Complete the Spotify authorization flow for the scopes:
   - `playlist-modify-public`
   - `playlist-modify-private`
8. After authorization succeeds, Spotipy will write a cache file named:
   - `/home/runner/work/KEXP/KEXP/.cache-<spotify_username>`
9. Open that cache file and copy the value of `refresh_token`.

## Update GitHub with the new token

1. Open the repository settings on GitHub.
2. Go to **Settings → Environments → weekly update**.
3. Update the environment secret named `SPOTIFY_REFRESH_TOKEN` with the new `refresh_token` value.
4. Confirm the other Spotify values are still correct:
   - secret: `SPOTIPY_CLIENT_ID`
   - secret: `SPOTIPY_CLIENT_SECRET`
   - variable: `SPOTIPY_REDIRECT_URI`
   - variable: `SPOTIFY_USERNAME`
   - variable: `PLAYLIST_NAME`

## Verify the fix

1. Re-run the **Weekly KEXP Catalog Update** workflow manually.
2. Confirm the `Run KEXP catalog processing` step succeeds.
3. If it still fails with `invalid_grant`, check for one of these mismatches:
   - wrong Spotify app client ID or secret
   - redirect URI in GitHub does not exactly match the Spotify app settings
   - token generated for a different Spotify user
   - Spotify access for the app was revoked and needs to be re-authorized again

## Clean up local secrets

After updating GitHub, remove any local files that contain secrets if you do not need them anymore, especially:

- `/home/runner/work/KEXP/KEXP/config.json`
- `/home/runner/work/KEXP/KEXP/.cache-<spotify_username>`
