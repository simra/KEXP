# GitHub Actions Setup for KEXP Catalog Processor

This repository includes a GitHub Actions workflow that automatically runs the KEXP catalog processor on a weekly schedule.

## Required GitHub Secrets

To set up the workflow, you need to add the following secrets to your GitHub repository:

### Navigation
1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret** for each secret below

### Required Secrets

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `SPOTIPY_CLIENT_ID` | Your Spotify App Client ID | `1ce5078ae2e544c29fd3c2ce1e4397b4` |
| `SPOTIPY_CLIENT_SECRET` | Your Spotify App Client Secret | `1ccdf3dd6832412aa801d01fddb03c91` |
| `SPOTIFY_REDIRECT_URI` | Spotify App Redirect URI | `http://localhost:8888/callback` |
| `SPOTIPY_REFRESH_TOKEN` | **REQUIRED** - Spotify Refresh Token (see instructions below) | `AQC...` (long string) |
| `SPOTIFY_USERNAME` | Your Spotify username | `simra73` |
| `PLAYLIST_NAME` | Name of the playlist to update | `KEXP Weekly` |
| `DAYS_TO_PARSE` | Number of days to parse (optional, default: 14) | `14` |
| `TOP_N` | Number of top tracks (optional, default: 100) | `100` |
| `PIVOT` | Pivot type (optional, default: track) | `track` |

### Getting Spotify App Credentials

1. Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
2. Create a new app (or use existing one)
3. Note down the **Client ID** and **Client Secret**
4. **IMPORTANT**: Add **exactly** `http://localhost:8888/callback` to the Redirect URIs in your app settings
   - Click "Edit Settings" 
   - In "Redirect URIs" section, add: `http://localhost:8888/callback`
   - Click "Save" at the bottom

### Troubleshooting "INVALID_CLIENT" Error

If you get "INVALID_CLIENT: Insecure redirect URI" error:

1. **Check exact URI match**: The redirect URI in your Spotify app **must exactly match** what's in your config
2. **Use the recommended URI**: `http://localhost:8888/callback` (this is Spotify's standard for local development)
3. **Wait a few minutes**: Spotify app changes can take 1-2 minutes to propagate
4. **Clear browser cache**: Or use incognito mode when testing

### Getting the Refresh Token

The refresh token is required for headless authentication in GitHub Actions. You need to get this token once by running authentication locally:

#### Easy Method (Recommended)

1. **Use the helper script:**
   ```bash
   python get_refresh_token.py
   ```

2. **Complete the OAuth flow:**
   - A browser window will open automatically
   - Log into Spotify and authorize the app
   - The script will display your refresh token

3. **Add the refresh token to GitHub secrets:**
   Copy the displayed refresh token and add it as the `SPOTIPY_REFRESH_TOKEN` secret in GitHub.

#### Manual Method

1. **Run the main script locally once:**
   ```bash
   python processCatalog.py
   ```

2. **Complete the OAuth flow and find the token:**
   After authentication, check the cache file (`.cache-{username}`) for the `refresh_token` value.

## Workflow Schedule

The workflow runs:
- **Automatically**: Every Sunday at 9:00 AM UTC
- **Manually**: You can trigger it manually from the Actions tab

## Manual Trigger

To run the workflow manually:
1. Go to the **Actions** tab in your GitHub repository
2. Select **Weekly KEXP Catalog Update**
3. Click **Run workflow**

## Security Notes

- The workflow creates a temporary `config.json` file during execution
- The config file is automatically deleted after the job completes (whether successful or failed)
- Secrets are never logged or exposed in the workflow output
- The original `config.json` file remains excluded from version control