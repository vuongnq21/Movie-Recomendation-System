# main.py
import streamlit as st
from streamlit_option_menu import option_menu
import psycopg2

import home
import detail
import account
import user_collection
import history

# --- Kết nối database, dùng cache để giảm số lần tạo kết nối ---


@st.cache_resource
def init_connection():
    # Hàm khởi tạo kết nối PostgreSQL, đọc từ st.secrets
    try:
        return psycopg2.connect(
            host=st.secrets["database"]["host"],
            port=st.secrets["database"]["port"],
            dbname=st.secrets["database"]["dbname"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"]
        )
    except Exception as e:
        st.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
        st.error(
            "Lưu ý khi deploy:\n"
            "1) Thêm IP '0.0.0.0/0' vào Render.\n"
            "2) Đảm bảo secrets.toml đã được thêm vào Streamlit Cloud."
        )
        return None


# --- Lấy kết nối ---
conn = init_connection()

# --- Chỉ chạy app khi kết nối thành công ---
if conn:

    # --- Sidebar menu ---
    with st.sidebar:
        selected_page = option_menu(
            menu_title='',
            options=['Home', 'Account', 'Collection', 'History'],
            icons=['house', 'person-circle', 'film', 'journal-check'],
            default_index=0,
            styles={
                "container": {"padding": "5px !important", "background-color": "#0E1117"},
                "icon": {"color": "white", "font-size": "18px"},
                "nav-link": {
                    "color": "#E0E0E0",
                    "font-size": "18px",
                    "text-align": "left",
                    "margin": "0px"
                }
            }
        )

    # --- Điều hướng trang ---
    # Nếu user đã chọn một movie, ưu tiên trang chi tiết
    if st.session_state.get('selected_movie'):
        detail.detail(conn)

    # Điều hướng mặc định theo menu
    elif selected_page == "Home":
        home.home(conn)

    elif selected_page == "Account":
        account.user_auth(conn)

    elif selected_page == "Collection":
        user_collection.display_collection(conn)

    elif selected_page == "History":
        history.display_history(conn)

# --- Trường hợp không kết nối được database ---
else:
    st.error("Ứng dụng không thể khởi động do lỗi kết nối cơ sở dữ liệu.")
