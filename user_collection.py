# user_collection.py
import streamlit as st

# --- import fetch_poster ---
try:
    from app import fetch_poster
except ImportError:
    st.error("Lỗi: Không tìm thấy file 'app.py' chứa hàm 'fetch_poster'.")

    def fetch_poster(id):
        return "https://via.placeholder.com/500x750.png?text=Error"

# --- Lấy danh sách phim trong bộ sưu tập ---


def get_user_collection(conn, user_id):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT movie_id, title FROM collections 
                WHERE user_id = %s
            """, (user_id,))
            movies = cursor.fetchall()
            return movies
    except Exception as e:
        st.error(f"Lỗi CSDL: {e}")
        return []

# --- Xóa phim khỏi bộ sưu tập ---


def remove_from_collection(conn, user_id, movie_id):
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM collections 
                WHERE user_id = %s AND movie_id = %s
            """, (user_id, movie_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Lỗi CSDL khi xóa phim: {e}")
        return False

# --- Hiển thị bộ sưu tập yêu thích ---


def display_collection(conn):

    # Kiểm tra đăng nhập
    if 'logged_in' not in st.session_state or not st.session_state.get('logged_in', False):
        st.error("Đăng nhập để xem bộ sưu tập!")
        return

    user_id = st.session_state['user_id']
    movies = get_user_collection(conn, user_id)

    if not movies:
        st.info("Bạn chưa thêm phim nào vào bộ sưu tập.")
        return

    st.title("Bộ sưu tập phim của bạn")

    # --- Hiển thị từng phim ---
    for movie in movies:
        movie_id, title = movie

        poster_url = fetch_poster(movie_id)

        col1, col2 = st.columns([1, 3])

        with col1:
            st.image(poster_url, width=150)

        with col2:
            st.write(f"**{title}**")

            # --- Xem chi tiết ---
            if st.button("Xem chi tiết", key=f"detail_{movie_id}"):
                st.session_state.selected_movie = (title, movie_id)
                st.session_state.current_page = 'Detail'
                st.rerun()

            # --- Xóa khỏi bộ sưu tập ---
            if st.button("Xóa", key=f"remove_{movie_id}"):
                if remove_from_collection(conn, user_id, movie_id):
                    st.success(f"Đã xóa phim '{title}' khỏi bộ sưu tập.")
                    st.rerun()
                else:
                    st.error(f"Không thể xóa phim '{title}' khỏi bộ sưu tập.")
