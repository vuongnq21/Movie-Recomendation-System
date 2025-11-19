import streamlit as st
import hashlib
import psycopg2


# --- comment --- Hàm mã hóa mật khẩu bằng SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


# --- comment --- Kiểm tra tên người dùng và mật khẩu khi đăng nhập
def authenticate_user(conn, username, password):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        # --- comment --- Nếu tìm thấy user và mật khẩu đúng
        if user:
            # user[2] = password đã mã hóa trong DB
            if user[2] == hash_password(password):
                return True, user[0]  # user[0] = user_id
        return False, None


# --- comment --- Hàm đăng ký người dùng mới
def register_user(conn, username, password):
    with conn.cursor() as cursor:
        hashed_password = hash_password(password)

        try:
            # --- comment --- Insert user mới, password đã được hash
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed_password)
            )
            conn.commit()
            st.success("Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ.")
        except psycopg2.errors.UniqueViolation:
            # --- comment --- Lỗi trùng username trong database
            st.error("Tên người dùng đã tồn tại. Vui lòng chọn tên khác.")
            conn.rollback()


# --- comment --- Hàm chính xử lý giao diện đăng nhập / đăng ký
def user_auth(conn):

    # --- comment --- Kiểm tra nếu người dùng đã đăng nhập
    if 'username' in st.session_state:

        st.title("Tài khoản")
        st.write(f"Chào mừng trở lại, **{st.session_state['username']}**!")

        # --- comment --- Nút đăng xuất
        if st.button("Đăng xuất"):
            del st.session_state['username']
            del st.session_state['user_id']
            st.session_state['logged_in'] = False
            st.success("Bạn đã đăng xuất thành công!")
            st.rerun()  # --- comment --- Reload UI sau khi logout

        return  # --- comment --- ĐÃ đăng nhập thì không hiển thị form nữa

    # --- comment --- Nếu chưa đăng nhập
    st.title("Đăng nhập / Đăng ký")

    if 'auth_option' not in st.session_state:
        st.session_state.auth_option = "Đăng nhập"

    auth_option = st.selectbox(
        "Chọn hành động",
        ["Đăng nhập", "Đăng ký"],
        index=["Đăng nhập", "Đăng ký"].index(st.session_state.auth_option)
    )
    st.session_state.auth_option = auth_option

    # --- comment --- Dùng form để tránh rerun liên tục khi gõ chữ
    if auth_option == "Đăng nhập":

        with st.form(key="login_form"):
            username = st.text_input("Tên người dùng")
            password = st.text_input("Mật khẩu", type="password")
            submit_button = st.form_submit_button("Đăng nhập")

            if submit_button:
                # --- comment --- Kiểm tra đủ dữ liệu
                if username and password:
                    success, user_id = authenticate_user(
                        conn, username, password)

                    if success:
                        # --- comment --- Lưu session khi đăng nhập thành công
                        st.session_state['username'] = username
                        st.session_state['user_id'] = user_id
                        st.success(f"Chào mừng trở lại, {username}!")
                        st.session_state['logged_in'] = True
                        st.rerun()  # --- comment --- Reload UI để chuyển sang trạng thái đã login
                    else:
                        st.error(
                            "Tên người dùng hoặc mật khẩu không đúng. Vui lòng thử lại.")
                else:
                    st.error("Vui lòng nhập đầy đủ tên người dùng và mật khẩu.")

    # --- comment --- Form đăng ký người dùng
    elif auth_option == "Đăng ký":

        with st.form(key="register_form"):
            username = st.text_input("Tên người dùng mới")
            password = st.text_input("Mật khẩu", type="password")
            confirm_password = st.text_input(
                "Xác nhận mật khẩu", type="password")
            submit_button = st.form_submit_button("Đăng ký")

            if submit_button:

                # --- comment --- Kiểm tra nhập đủ
                if username and password and confirm_password:
                    if password == confirm_password:
                        register_user(conn, username, password)
                    else:
                        st.error(
                            "Mật khẩu và xác nhận mật khẩu không khớp. Vui lòng thử lại.")
                else:
                    st.error("Vui lòng nhập đầy đủ các trường.")
