import streamlit as st
import pandas as pd
import pickle
from difflib import get_close_matches
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


import os

print("Current working directory:", os.getcwd())
print("Files in directory:", os.listdir())

#CSV_PATH = "/Users/rnegilxm162004/Documents/pythonProject2/spotify-project/spotify_clean.csv"
#MODEL_PATH = "/Users/rnegilxm162004/Documents/pythonProject2/spotify-project/spotify_model.pkl"

CSV_PATH = "spotify_clean.csv"
MODEL_PATH = "spotify_model.pkl"

@st.cache_data
def load_data():
    return pd.read_csv(CSV_PATH)

@st.cache_resource 
def load_model(): 
    with open(MODEL_PATH, "rb") as f: 
        return pickle.load(f)
    
df = load_data()
model = load_model()
print("Dataframe loaded:", df.shape)

CLIENT_ID = "bc75b2d0fed5450cabf4421851fb3529"
CLIENT_SECRET = "970bb52cf518478daff8742c2861edbf"



sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
)



features = ['danceability', 'energy', 'valence', 'tempo',
            'acousticness', 'instrumentalness', 'liveness', 'speechiness']

SONG_COL = "track_name" if "track_name" in df.columns else "name"
ARTIST_COL = "artist_name" if "artist_name" in df.columns else "artists"


def recommend(song_name, n_recs=5):
    if song_name not in df[SONG_COL].values:
        return pd.DataFrame()

    song_features = df[df[SONG_COL] == song_name][features].values[0]
    distances, indices = model.kneighbors([song_features])
    recs = df.iloc[indices[0][1:n_recs+1]][[SONG_COL, ARTIST_COL] + features]
    return recs


def fetch_spotify_data(song_name, artist=None):
    query = f"{song_name} {artist}" if artist else song_name
    results = sp.search(q=query, limit=1, type="track")
    if results["tracks"]["items"]:
        track = results["tracks"]["items"][0]
        return {
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "album": track["album"]["name"],
            "cover": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "preview": track["preview_url"],
            "spotify_url": track["external_urls"]["spotify"]
        }
    return None


st.title("🎶 Advanced Spotify Recommender")
st.write("Discover your next favorite track with previews and album art!")

n_recs = st.slider("🎧 Number of recommendations:", 3, 10, 5)
song_input = st.text_input("🔍 Enter a song name:")

if song_input:
    matches = get_close_matches(song_input, df[SONG_COL].dropna().unique(), n=1, cutoff=0.5)

    if matches:
        selected_song = matches[0]
        st.success(f"Showing recommendations for: **{selected_song}**")

        recs = recommend(selected_song, n_recs=n_recs)

        if not recs.empty:
 
            for _, row in recs.iterrows():
                data = fetch_spotify_data(row[SONG_COL], row[ARTIST_COL])

                if data:
                    st.subheader(f"🎵 {data['name']} — {data['artist']}")
                    if data["cover"]:
                        st.image(data["cover"], width=200)
                    if data["preview"]:
                        st.audio(data["preview"])
                    st.markdown(f"[▶️ Open in Spotify]({data['spotify_url']})")
                else:
                    st.write(f"{row[SONG_COL]} — {row[ARTIST_COL]}")
        else:
            st.warning("No recommendations found.")
    else:
        st.error("❌ No matching song found. Try another name.")