# history.py
import streamlit as st
import requests

try:
    from app import fetch_poster
except ImportError:
    st.error("Lỗi: Không tìm thấy file 'app.py' chứa hàm 'fetch_poster'.")
    def fetch_poster(id):
        return "https://via.placeholder.com/500x750.png?text=Error"

def get_user_purchase_history(conn, user_id):
    """Lấy lịch sử mua phim của người dùng từ cơ sở dữ liệu"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT movie_id, title, amount FROM purchases
                WHERE user_id = %s
                ORDER BY purchase_date DESC
            """, (user_id,))
            movies = cursor.fetchall()
            return movies
    except Exception as e:
        st.error(f"Lỗi CSDL khi sắp xếp: {e}")
        conn.rollback()
        try:
            with conn.cursor() as cursor:
                st.warning("Không thể sắp xếp. Đang thử tải mà không sắp xếp...")
                cursor.execute("""
                    SELECT movie_id, title, amount FROM purchases
                    WHERE user_id = %s
                """, (user_id,))
                movies = cursor.fetchall()
                return movies
        except Exception as e2:
            st.error(f"Lỗi CSDL nghiêm trọng: {e2}")
            return []


# --- HÀM ĐÃ ĐƯỢC SỬA (LOẠI BỎ CÁC THÔNG BÁO) ---
def get_film_details_from_tmdb(tmdb_id):
    """
    Thử gọi API phimapi.com.
    Trả về link 'embed' nếu tìm thấy, hoặc None nếu thất bại.
    """
    
    types_to_try = ['movie', 'tv']
    
    for film_type in types_to_try:
        api_url = f"https://phimapi.com/tmdb/{film_type}/{tmdb_id}"
        
        try:
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 404:
                continue 
                
            response.raise_for_status() 
            
            data = response.json()
            
            try:
                embed_link = data['episodes'][0]['server_data'][0]['link_embed']
                return embed_link # Trả về link và kết thúc hàm
            
            except (KeyError, IndexError, TypeError) as e:
                st.error(f"Lỗi trích xuất link: Cấu trúc JSON không đúng. Lỗi: {e}")
                st.json(data) # Vẫn hiển thị data lỗi để debug
                return None 

        except requests.exceptions.HTTPError as err:
            st.error(f"Lỗi HTTP: {err}")
            continue 
        except requests.exceptions.RequestException as e:
            st.error(f"Lỗi kết nối API: {e}")
            return None 

    # Nếu chạy hết vòng lặp mà không return
    st.error(f"Không tìm thấy phim với ID {tmdb_id} cho cả 'movie' và 'tv'.")
    return None


# --- HÀM ĐÃ ĐƯỢC SỬA (ĐỂ HIỂN THỊ LINK) ---
def display_history(conn):
    """Hiển thị lịch sử mua phim của người dùng"""
    
    # Sử dụng session_state để lưu link nào đang được hiển thị
    if 'link_to_show' not in st.session_state:
        st.session_state.link_to_show = {}

    if 'logged_in' not in st.session_state or not st.session_state.get('logged_in', False):
        st.error("Đăng nhập để xem lịch sử mua hàng!")
        return

    user_id = st.session_state['user_id']
    movies = get_user_purchase_history(conn, user_id)

    if not movies:
        st.info("Bạn chưa mua phim nào.")
        return

    st.title("Lịch sử mua phim của bạn")

    for movie in movies:
        tmdb_id, title, amount = movie 
        poster_url = fetch_poster(tmdb_id) 
        
        col1, col2 = st.columns([1, 3]) 
        with col1:
            st.image(poster_url, width=150) 
        with col2:
            st.write(f"**{title}**") 
            st.write(f"Giá mua: {amount:,.0f} VNĐ")
            
            # --- LOGIC NÚT BẤM ĐÃ THAY ĐỔI ---
            if st.button(f"Lấy link phim", key=f"get_link_{tmdb_id}"):
                
                # 1. Gọi hàm (đã "tắt tiếng") để lấy link
                movie_link = get_film_details_from_tmdb(tmdb_id)
                
                # 2. Lưu link vào session state (sẽ lưu link hoặc None)
                st.session_state.link_to_show[tmdb_id] = movie_link
            
            # --- HIỂN THỊ LINK NẾU CÓ TRONG STATE ---
            # Kiểm tra xem có link cho tmdb_id này trong state không
            if st.session_state.link_to_show.get(tmdb_id):
                link = st.session_state.link_to_show[tmdb_id]
                
                # Streamlit tự động biến text URL thành link
                st.write(link)