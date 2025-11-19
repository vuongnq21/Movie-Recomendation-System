# detail.py
import streamlit as st

from app import (
    recommend_content_based,
    fetch_poster,
    fetch_movie_details,
    fetch_trailer_key,
    fetch_credits
)

# --- Kiểm tra phim trong bộ sưu tập ---


def check_movie_in_collection(conn, user_id, movie_id):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM collections 
                WHERE user_id = %s AND movie_id = %s
            """, (user_id, movie_id))
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        st.error(f"Lỗi CSDL khi kiểm tra phim: {e}")
        return False

# --- Lưu phim vào bộ sưu tập ---


def save_to_collection(conn, user_id, movie_id, title):
    if check_movie_in_collection(conn, user_id, movie_id):
        return False, f"Phim '{title}' đã có trong bộ sưu tập!"

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO collections (user_id, movie_id, title) 
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, movie_id) DO NOTHING
            """, (user_id, movie_id, title))
        conn.commit()
        return True, f"Đã thêm '{title}' vào Bộ Sưu Tập!"
    except Exception as e:
        conn.rollback()
        return False, f"Lỗi CSDL: {e}"

# --- Xử lý mua phim ---


def process_purchase(conn, user_id, movie_id, title):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM purchases 
                WHERE user_id = %s AND movie_id = %s
            """, (user_id, movie_id))
            existing_purchase = cursor.fetchone()

        if existing_purchase:
            return False, f"Bạn đã mua '{title}' rồi!"

        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO purchases (user_id, movie_id, title, amount)
                VALUES (%s, %s, %s, %s)
            """, (user_id, movie_id, title, 99000))
        conn.commit()

        return True, f"Mua '{title}' thành công!"

    except Exception as e:
        conn.rollback()
        return False, f"Lỗi CSDL: {e}"

# --- Giao diện trang chi tiết phim ---


def detail(conn):
    st.header("Movie Recommendation System")

    selected_title, selected_tmdbId = st.session_state.selected_movie

    # --- Nút quay lại ---
    if st.button("BACK"):
        st.session_state.selected_movie = None
        st.session_state.current_page = 'Home'
        st.rerun()

    st.title(selected_title)

    # --- Lấy thông tin phim ---
    details = fetch_movie_details(selected_tmdbId)
    trailer_key = fetch_trailer_key(selected_tmdbId)
    director_name = fetch_credits(selected_tmdbId)

    col1, col2 = st.columns([1, 2])

    # --- Cột trái: poster + các nút ---
    with col1:
        st.image(fetch_poster(selected_tmdbId))

        buy_col, fav_col = st.columns(2)

        # --- Nút mua phim ---
        with buy_col:
            if st.button("Mua phim ", key="buy_movie"):
                if st.session_state.get('logged_in', False):
                    user_id = st.session_state.user_id

                    movie_id_int = int(selected_tmdbId)

                    success, message = process_purchase(
                        conn, user_id, movie_id_int, selected_title)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("Bạn cần đăng nhập để mua phim!")

        # --- Nút thêm vào bộ sưu tập ---
        with fav_col:
            if st.button("Yêu thích", key="like_movie"):
                if st.session_state.get('logged_in', False):
                    user_id = st.session_state.user_id

                    movie_id_int = int(selected_tmdbId)

                    success, message = save_to_collection(
                        conn, user_id, movie_id_int, selected_title)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("Bạn cần đăng nhập để thêm vào Bộ Sưu Tập!")

    # --- Cột phải: thông tin chi tiết ---
    with col2:
        st.write(f"**Đạo diễn:** {director_name}")
        st.write(f"**Quốc gia:** {details.get('country', 'N/A')}")
        st.write(f"**Giới thiệu:** {details.get('overview', 'N/A')}")

    # --- Trailer ---
    st.subheader("Trailer")
    if trailer_key:
        st.video(f"https://www.youtube.com/watch?v={trailer_key}")
    else:
        st.warning("Không tìm thấy trailer.")

    st.markdown("---")

    # --- Phim tương tự ---
    st.subheader("Phim tương tự")

    movie_name, movie_poster, movie_id = recommend_content_based(
        selected_title)

    if movie_name:
        cols_rec = st.columns(5)
        for i in range(5):
            with cols_rec[i]:
                st.image(movie_poster[i])
                st.button(
                    movie_name[i],
                    key=f"rec_detail_{i}",
                    on_click=st.session_state.set_selected_movie_func,
                    args=(movie_name[i], movie_id[i])
                )
    else:
        st.write("Không tìm thấy đề xuất cho phim này.")
