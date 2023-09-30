import re
import csv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from utils import get_config, Logger
from tqdm import tqdm  # Import tqdm for the progress bar

class Spotify:
    def __init__(self, config_location):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=get_config(config_location)["client_id"],
                                                client_secret=get_config(config_location)["client_secret"],
                                                redirect_uri='http://localhost:8080/callback',
                                                scope='playlist-modify-private playlist-modify-public'))
        
    def search_track(self, artist, song):
        query = f'artist:{artist} track:{song}'
        results = self.sp.search(q=query, limit=1)
        if results['tracks']['items']:
            return results['tracks']['items'][0]['uri']
        else:
            return None
        
    def create_playlist(self, name):
        user_id = self.sp.me()['id']
        playlist = self.sp.user_playlist_create(user=user_id, name=name, public=False)
        return playlist['id']
    
    def add_track_to_playlist(self, playlist_id, track_uri):
        self.sp.playlist_add_items(playlist_id, [track_uri])

# Define the expression used for the search
def find(text, PRINT=True):
    if text == " " or None or len(text) == 0:
        return False
    if isinstance(text, list):
        text = text[0]
    result = text.split("–")
    song = result[1][1:]
    artist = result[0].split(" ")[1] + " " + result[0].split(" ")[2]
    if PRINT: print(f"Artist: {artist}, Song: {song}")
    return song, artist


# Open the source.txt file for reading
def read(source='source.csv'):
    with open(source, 'r', encoding="utf8") as file:
        reader = csv.reader(file)
        result = list()
        for text in reader:
            value = find(text)
            if isinstance(value, bool):
                pass
            else:
                result.append(tuple(value))
    return result

# Write the data back into a table
def write(result):
    with open('result.csv', 'w', encoding='utf8') as file:
        writer = csv.writer(file)
        for item in result:
            writer.writerow(item)

def push_to_spotify(data, PLAYLIST_NAME="Testing playlist", CONFIG_FILE= "config.json", KEEP_ORDER=True):
    # Initialise the SpotiPy client using the Spotify class
    spotify = Spotify(CONFIG_FILE)

    # Create playlist based on user function variables
    playlist_id = spotify.create_playlist(PLAYLIST_NAME)

    # Clean the playlist itself from duplicates
    def clean_duplicates(data):
        result = list()
        for item in data:
            if item in result:
                logger.write(log_type="warning", data=(f"Duplicate URI's found in exported list, usually meaning duplicated songs, ID: {item}"))
            else:
                result.append(item)
        return result
    data = clean_duplicates(data)

    # Get URI's from result data list
    uri = list()
    progress_bar = tqdm(total=len(data), desc="Searching for your songs: ")
    for item in data:
        uri.append(spotify.search_track(item[1], item[0]))
        progress_bar.update(1)
    progress_bar.close()

    # Trigger warning if duplicate URI's detected
    if len(set(uri)) < len(uri):
        logger.write(log_type="warning", data=("Duplicate URI's found in exported list, usually meaning duplicated songs."))
    fixed_uri = list()

    # Clean the list from NoneTypes
    for item in uri:
        if item is not None:
            fixed_uri.append(item)
        else:
            logger.write(log_type="warning", data=(f"NoneTypes was found, usually meaning unidentified songs, ID: {item}"))

    # Push clean data to made playlist
    if not KEEP_ORDER: spotify.sp.playlist_add_items(playlist_id, fixed_uri)
    else: 
        for item in fixed_uri:
            spotify.sp.playlist_add_items(playlist_id, [item])

if __name__ == "__main__":
    global logger
    logger = Logger()
    result = read()
    write(result)
    push_to_spotify(result, CONFIG_FILE=r"D:\Dokumenty\Klíče\yt2spotify_config.json")

