import streamlit as st
import pickle
import requests
import pandas as pd
import os

# --- Đường dẫn file gốc ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- HÀM LẤY PHIM PHỔ BIẾN ---
@st.cache_data(show_spinner=False)
def fetch_popular_movies():
    # Lấy API key từ st.secrets
    api_key = st.secrets["tmdb"]["api_key"]
    URL = f"https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page=1"

    pop_names = []
    pop_posters = []

    try:
        data = requests.get(URL)
        data.raise_for_status()

        results = data.json().get("results", [])

        for movie in results[:10]:
            pop_names.append(movie["title"])
            poster_path = movie.get("poster_path")

            if poster_path:
                full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
                pop_posters.append(full_path)
            else:
                pop_posters.append("https://via.placeholder.com/500x750.png?text=No+Poster")

        return pop_names, pop_posters

    except Exception as e:
        print(f"Lỗi khi lấy phim phổ biến: {e}")
        return [], []


# --- HÀM LẤY POSTER ---
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id):
    api_key = st.secrets["tmdb"]["api_key"]
    URL = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"

    try:
        data = requests.get(URL)
        data.raise_for_status()

        poster_path = data.json().get("poster_path", None)

        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
        else:
            return "https://via.placeholder.com/500x750.png?text=No+Poster"

    except Exception as e:
        print(f"Error fetching poster for {movie_id}: {e}")
        return "https://via.placeholder.com/500x750.png?text=Error"


# --- LOAD MODEL ĐỀ XUẤT ---
@st.cache_resource(show_spinner=False)
def load_data():
    movies_master_path = os.path.join(BASE_DIR, "content_based_model", "movies_list.pkl")
    similarity_cb_path = os.path.join(BASE_DIR, "content_based_model", "similarity.pkl")

    # Kiểm tra file tồn tại
    if not os.path.exists(movies_master_path) or not os.path.exists(similarity_cb_path):
        st.error("Lỗi: Không tìm thấy file .pkl trong thư mục 'content_based_model'.")
        st.error("Hãy kiểm tra lại GitHub.")
        return None, None

    movies_master = pickle.load(open(movies_master_path, "rb"))
    similarity_cb = pickle.load(open(similarity_cb_path, "rb"))

    return movies_master, similarity_cb


# --- HÀM ĐỀ XUẤT PHIM DỰA TRÊN NỘI DUNG ---
@st.cache_data(show_spinner=False)
def recommend_content_based(movie):
    movies_master, similarity_cb = load_data()

    if movies_master is None or similarity_cb is None:
        return [], [], []

    movie_entry = movies_master[movies_master["title"] == movie]
    if movie_entry.empty:
        return [], [], []

    index = movie_entry.index[0]

    distance = sorted(
        list(enumerate(similarity_cb[index])),
        reverse=True,
        key=lambda vector: vector[1]
    )

    recommend_movie = []
    recommend_poster = []
    recommend_movie_ids = []

    for i in distance[1:6]:
        movies_id = movies_master.iloc[i[0]].tmdbId

        recommend_movie.append(movies_master.iloc[i[0]].title)
        recommend_poster.append(fetch_poster(movies_id))
        recommend_movie_ids.append(movies_id)

    return recommend_movie, recommend_poster, recommend_movie_ids


# --- HÀM HIỂN THỊ PHIM ---
def show_movies(names, posters):
    cols = st.columns(5)

    for i, col in enumerate(cols):
        col.image(posters[i])
        col.text(names[i])


# --- HÀM LẤY CHI TIẾT PHIM ---
@st.cache_data(show_spinner=False)
def fetch_movie_details(movie_id):
    api_key = st.secrets["tmdb"]["api_key"]
    URL = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"

    try:
        data = requests.get(URL)
        data.raise_for_status()

        details = data.json()
        countries = details.get("production_countries", [])

        country_name = "N/A"
        if countries:
            country_name = countries[0].get("name", "N/A")

        return {
            "overview": details.get("overview", "Chưa có giới thiệu."),
            "country": country_name
        }

    except Exception as e:
        print(f"Lỗi khi lấy chi tiết phim {movie_id}: {e}")
        return {}


# --- HÀM LẤY TRAILER PHIM ---
@st.cache_data(show_spinner=False)
def fetch_trailer_key(movie_id):
    api_key = st.secrets["tmdb"]["api_key"]
    URL = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}&language=en-US"

    try:
        data = requests.get(URL)
        data.raise_for_status()

        videos = data.json().get("results", [])

        for video in videos:
            if video["site"] == "YouTube" and video["type"] == "Trailer":
                return video["key"]

        return None

    except Exception as e:
        print(f"Lỗi khi lấy trailer {movie_id}: {e}")
        return None


# --- HÀM LẤY TÊN ĐẠO DIỄN ---
@st.cache_data(show_spinner=False)
def fetch_credits(movie_id):
    api_key = st.secrets["tmdb"]["api_key"]
    URL = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={api_key}&language=en-US"

    try:
        data = requests.get(URL)
        data.raise_for_status()

        all_crew = data.json().get("crew", [])
        director_name = "N/A"

        for crew in all_crew:
            if crew.get("job") == "Director":
                director_name = crew.get("name", "N/A")
                break

        return director_name

    except Exception as e:
        print(f"Lỗi khi lấy đạo diễn {movie_id}: {e}")
        return "N/A"
