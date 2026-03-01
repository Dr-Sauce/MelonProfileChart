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
    
    # Extract Song, Artist, and Album for fallback
    search_data = []
    for item in data.get('contents', {}).get('songList', []):
        name = item.get('songName')
        artist = item.get('artistList', [{}])[0].get('artistName')
        album = item.get('albumName')
        if name and artist:
            search_data.append({
                "primary": f"{name} {artist}",
                "fallback": f"{album} {artist}" if album else None
            })

    # 2. Authenticate with Spotify
    auth_manager = SpotifyOAuth(
        client_id=os.environ['SPOTIFY_CLIENT_ID'],
        client_secret=os.environ['SPOTIFY_CLIENT_SECRET'],
        redirect_uri='http://127.0.0.1:8080/callback',
        scope='playlist-modify-public'
    )

    try:
        token_info = auth_manager.refresh_access_token(os.environ['SPOTIFY_REFRESH_TOKEN'])
        sp = spotipy.Spotify(auth=token_info['access_token'])
    except Exception as e:
        print(f"Auth Error: {e}")
        return

    # 3. Search Logic
    track_uris = []
    for item in search_data:
        # Step A: Try primary search
        result = sp.search(q=item['primary'], type='track', limit=1)
        tracks = result['tracks']['items']
        
        # Step B: If Primary fails, try Fallback (Album + Artist)
        if not tracks and item['fallback']:
            print(f"Primary failed for: {item['primary']}. Trying fallback: {item['fallback']}")
            result = sp.search(q=item['fallback'], type='track', limit=1)
            tracks = result['tracks']['items']

        # Step C: Grab the first result found in either step
        if tracks:
            # We don't check the title here—if Spotify says it's the top result, we take it.
            track_uris.append(tracks[0]['uri'])
            print(f"Added: {tracks[0]['name']} (Query: {item['primary']})")
        else:
            print(f"Could not find anything for: {item['primary']}")

    # 4. Replace Playlist Content
    if track_uris:
        # Spotify API allows up to 100 tracks per replacement
        sp.playlist_replace_items(PLAYLIST_ID, track_uris[:100])
        print(f"\nSuccess! Updated playlist with {len(track_uris[:100])} tracks.")
    else:
        print("No tracks found to add.")

if __name__ == "__main__":
    main()
