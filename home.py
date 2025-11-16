# home.py
import streamlit as st
import pandas as pd

from app import (
    load_data,
    fetch_popular_movies,
    show_movies,
    recommend_content_based,
)

# --- Giao diện trang Home ---
def home(conn):

    # --- Quản lý trạng thái phim được chọn ---
    if 'selected_movie' not in st.session_state:
        st.session_state.selected_movie = None

    # --- Hàm cập nhật phim được chọn ---
    def set_selected_movie(title, tmdbId):
        st.session_state.selected_movie = (title, tmdbId)
        st.session_state.current_page = 'Detail'

    # Lưu function vào session_state để chỗ khác gọi được
    st.session_state.set_selected_movie_func = set_selected_movie

    # --- Giao diện chính ---
    st.header("Movie Recommendation System")

    # Load dữ liệu phim
    movies_master, _ = load_data()

    # Nếu chưa chọn phim → Hiển thị trang Home bình thường
    if st.session_state.selected_movie is None:

        # --- Trending ---
        st.subheader("Trending")
        pop_names, pop_posters = fetch_popular_movies()

        if pop_names:
            # Hiển thị 5 phim đầu
            show_movies(pop_names[:5], pop_posters[:5])
            # Hiển thị phần còn lại
            show_movies(pop_names[5:], pop_posters[5:])
        else:
            st.warning("Không thể tải danh sách phim phổ biến.")

        st.markdown("---")

        # --- Đề xuất theo nội dung ---
        st.subheader("Chọn phim yêu thích để nhận đề xuất")

        movies_list_cb = movies_master['title'].values
        selectvalue = st.selectbox(" ", movies_list_cb, key="cb_select")

        # --- Nhấn nút đề xuất ---
        if st.button("Show Recommendation", key="cb_button"):

            movie_name, movie_poster, movie_id = recommend_content_based(selectvalue)

            if movie_name:
                st.write("Phim đề xuất:")

                cols = st.columns(5)
                for i in range(5):
                    with cols[i]:
                        st.image(movie_poster[i])
                        st.button(
                            movie_name[i],
                            key=f"rec_{i}",
                            on_click=set_selected_movie,
                            args=(movie_name[i], movie_id[i])
                        )
            else:
                st.error("Không tìm thấy đề xuất cho phim này.")
