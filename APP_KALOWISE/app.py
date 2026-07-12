import streamlit as st
import page_menu
import page_orders
import page_revenue
import page_settings

# Cấu hình trang luôn phải nằm đầu tiên ở file gốc
st.set_page_config(page_title="Kalowise - Healthy Food", layout="wide", page_icon="🌿")

st.markdown("""
    <style>
    [data-testid="stContainer"] { border-radius: 15px; transition: transform 0.2s; }
    [data-testid="stContainer"]:hover { transform: translateY(-2px); }
    </style>
""", unsafe_allow_html=True)

# HỆ THỐNG TÀI KHOẢN
USERS = {
    "admin": {"pass": "admin123", "role": "Admin", "name": "Quản Lý (Admin)"},
    "ketoan": {"pass": "editor123", "role": "Editor", "name": "Kế Toán (Editor)"},
    "shipper": {"pass": "giao123", "role": "User", "name": "Giao Hàng (User)"}
}

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# MENU ĐIỀU HƯỚNG TỔNG (Sidebar)
st.sidebar.title("🌿 KALOWISE")
view_mode = st.sidebar.radio("CHUYỂN ĐỔI GIAO DIỆN", ["🛒 Đặt món", "🔐 Khu vực Quản trị"])
st.sidebar.markdown("---")

# ==========================================
# 1. GIAO DIỆN KHÁCH HÀNG (PUBLIC)
# ==========================================
if view_mode == "🛒 Đặt món":
    page_menu.render()

# ==========================================
# 2. GIAO DIỆN QUẢN TRỊ (PRIVATE)
# ==========================================
elif view_mode == "🔐 Khu vực Quản trị":
    
    # KIỂM TRA ĐĂNG NHẬP
    if not st.session_state.get("logged_in", False):
        st.markdown("<h1 style='text-align: center; color: #2E7D32;'>HỆ THỐNG NỘI BỘ KALOWISE</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.container(border=True):
                st.subheader("Đăng nhập hệ thống")
                # Dùng form để bắt sự kiện Enter tự động
                with st.form("login_form"):
                    username = st.text_input("👤 Tài khoản")
                    password = st.text_input("🔑 Mật khẩu", type="password")
                    submit = st.form_submit_button("Đăng nhập", use_container_width=True, type="primary")
                
                if submit:
                    if username in USERS and USERS[username]["pass"] == password:
                        st.session_state["logged_in"] = True
                        st.session_state["role"] = USERS[username]["role"]
                        st.session_state["display_name"] = USERS[username]["name"]
                        st.rerun()
                    else:
                        st.error("Sai tài khoản hoặc mật khẩu!")

    else:
        # HIỂN THỊ MENU ĐIỀU HƯỚNG BÊN TRONG SAU KHI ĐĂNG NHẬP
        role = st.session_state["role"]
        
        st.sidebar.success(f"👤 Xin chào, **{st.session_state['display_name']}**")
        
        menu_options = ["📦 Quản lý Đơn hàng"]
        if role in ["Admin", "Editor"]:
            menu_options.append("💰 Thống kê Doanh thu")
        if role == "Admin":
            menu_options.append("⚙️ Cài đặt Thực đơn")
            
        choice = st.sidebar.radio("CHỨC NĂNG NỘI BỘ", menu_options)
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Đăng xuất", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        # ĐIỀU HƯỚNG VÀO CÁC FILE CHỨC NĂNG TƯƠNG ỨNG
        if choice == "📦 Quản lý Đơn hàng":
            page_orders.render()
        elif choice == "💰 Thống kê Doanh thu":
            page_revenue.render()
        elif choice == "⚙️ Cài đặt Thực đơn":
            page_settings.render()
