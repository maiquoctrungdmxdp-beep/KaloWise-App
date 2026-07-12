import streamlit as st
import pandas as pd
from supabase import create_client, Client
import urllib.parse
import requests

# --- 1. KHỞI TẠO KẾT NỐI SUPABASE ---
# Dùng @st.cache_resource để kết nối này luôn được giữ mở, giúp app chạy mượt hơn
@st.cache_resource
def init_connection() -> Client:
    # Gán cứng URL và Key trực tiếp để trị dứt điểm lỗi Cache
    url = "https://wwijsgbnvqisbrvkvpts.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind3aWpzZ2JudnFpc2Jydmt2cHRzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MzgzNDA4NCwiZXhwIjoyMDk5NDEwMDg0fQ.MO1riM6HudMDsckqO-WFmLk6h4Q_FrnYsSRPn1NG9A0"
    return create_client(url, key)

# Tạo đối tượng supabase dùng chung cho toàn bộ app
supabase = init_connection()

# --- 2. HÀM TẢI ĐƠN HÀNG ---
@st.cache_data(ttl=15)
def load_orders():
    try:    
        # Hút toàn bộ dữ liệu từ bảng 'orders'
        response = supabase.table("orders").select("*").execute()
        df = pd.DataFrame(response.data)
        return df
    except Exception as e:
        st.error(f"Lỗi tải đơn hàng từ Supabase: {e}")
        return pd.DataFrame()

# --- 3. HÀM TẢI MENU (Thay cho Bảng Giá cũ) ---
@st.cache_data(ttl=15)
def load_prices():
    try:
        # Hút toàn bộ dữ liệu từ bảng 'menu'
        response = supabase.table("menu").select("*").execute()
        df = pd.DataFrame(response.data)
        return df
    except Exception as e:
        st.error(f"Lỗi tải menu từ Supabase: {e}")
        return pd.DataFrame()

# --- 4. HÀM TÍNH QUÃNG ĐƯỜNG (Giữ nguyên) ---
@st.cache_data(ttl=86400)
def get_distance_km(destination_address):
    headers = {'User-Agent': 'KalowiseApp/1.0'}
    clean_address = destination_address.replace("K", "", 1) if destination_address.startswith("K") else destination_address
    geocode_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(clean_address)}&format=json&limit=1"
    
    dest_lat, dest_lon = None, None
    try:
        res = requests.get(geocode_url, headers=headers).json()
        if len(res) > 0:
            dest_lat = float(res[0]['lat'])
            dest_lon = float(res[0]['lon'])
    except:
        pass
        
    if dest_lat is None or dest_lon is None:
        return -1.0 

    # Tọa độ quán tại Đà Nẵng
    shop_lat, shop_lon = 16.043804, 108.215882
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{shop_lon},{shop_lat};{dest_lon},{dest_lat}?overview=false"
    try:
        res_osrm = requests.get(osrm_url).json()
        if res_osrm.get("code") == "Ok":
            dist_meters = res_osrm["routes"][0]["distance"]
            return dist_meters / 1000.0
    except:
        pass
    return -1.0