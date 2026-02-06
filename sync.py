import os
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# --- CONFIGURATION ---
DATA_URL = "https://kkosvc.melon.com/mwk/chart/profile.json"
PLAYLIST_ID = "627NPPswPEFjI8xe5Y48D6"

def main():
    # 1. Fetch JSON data
    try:
        r = requests.get(DATA_URL)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"Error fetching Melon data: {e}")
        return
    
    # Extract song + artist names
    queries = []
    for item in data.get('contents', {}).get('songList', []):
        name = item.get('songName')
        artist = item.get('artistList', [{}])[0].get('artistName')
        if name and artist:
            queries.append(f"{name} {artist}")

    # 2. Authenticate with Spotify (The Fixed Part)
    # We don't pass the refresh_token here anymore
    auth_manager = SpotifyOAuth(
        client_id=os.environ['SPOTIFY_CLIENT_ID'],
        client_secret=os.environ['SPOTIFY_CLIENT_SECRET'],
        redirect_uri='http://127.0.0.1:8080/callback',
        scope='playlist-modify-public'
    )

    # Instead, we use the refresh_token here to get a fresh session
    try:
        token_info = auth_manager.refresh_access_token(os.environ['SPOTIFY_REFRESH_TOKEN'])
        sp = spotipy.Spotify(auth=token_info['access_token'])
    except Exception as e:
        print(f"Auth Error: Check your GitHub Secrets. Details: {e}")
        return

    # 3. Search for Spotify IDs
    track_uris = []
    for q in queries:
        result = sp.search(q=q, type='track', limit=1)
        items = result['tracks']['items']
        if items:
            track_uris.append(items[0]['uri'])
            print(f"Found: {q}")
        else:
            print(f"Not Found: {q}")

    # 4. Replace Playlist Content
    if track_uris:
        sp.playlist_replace_items(PLAYLIST_ID, track_uris[:100])
        print(f"Success! Updated playlist with {len(track_uris)} tracks.")
    else:
        print("No matching tracks found on Spotify.")

if __name__ == "__main__":
    main()
