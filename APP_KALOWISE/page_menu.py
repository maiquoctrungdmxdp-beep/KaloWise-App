import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, time
from utils import load_prices, get_distance_km, supabase

def render():
    st.title("📦 THỰC ĐƠN KALOWISE - ĐẶT MÓN")
    
    try:
        # 1. TẢI THỰC ĐƠN (Đọc từ bảng menu của Supabase)
        df_menu = load_prices()
        
        # Chỉ hiển thị các món "dang_ban == True"
        if not df_menu.empty:
            if 'dang_ban' in df_menu.columns:
                df_menu = df_menu[df_menu['dang_ban'] == True].copy()
            else:
                st.warning("Cấu trúc bảng database không đúng.")
                return
            
        if df_menu.empty:
            st.warning("Xin lỗi, thực đơn hôm nay tạm hết hoặc chưa có sẵn.")
            return

        # Ép kiểu dữ liệu an toàn cho giá tiền
        df_menu['gia_tien'] = pd.to_numeric(df_menu['gia_tien'], errors='coerce').fillna(0)

        # KHỞI TẠO GIỎ HÀNG (Sử dụng session_state.cart dictionary {mon_id: so_luong})
        if "cart" not in st.session_state:
            st.session_state.cart = {mon_id: 0 for mon_id in df_menu['id']}

        # ==========================================
        # GIAO DIỆN CHỌN MÓN (HIỂN THỊ DẠNG CỘT)
        # ==========================================
        st.header("🥢 Chọn món của bạn")
        cols = st.columns(3) # Hiển thị 3 cột
        
       # Dùng container nhỏ gọn hơn thay vì chia cột cố định
        for i, (index, row) in enumerate(df_menu.iterrows()):
            mon_id = row['id']
            ten_mon = str(row['ten_mon'])
            gia_tien = int(row['gia_tien'])
            qty = st.session_state.cart.get(mon_id, 0)
            with st.container(border=True):
                # Bố cục 2 phần: Tên món bên trái, Nút bấm bên phải
                c_info, c_qty = st.columns([1.5, 1]) 
                
                with c_info:
                    st.markdown(f"### {ten_mon}")
                    st.write(f"💰 **Giá:** {gia_tien:,.0f} đ")
                
                with c_qty:
                    # Bố cục 3 phần cho nút: Trừ - Số - Cộng
                    c1, c2, c3 = st.columns([1, 1, 1])
                    with c1:
                        if st.button("➖", key=f"minus_{mon_id}", disabled=(qty == 0), use_container_width=True):
                            st.session_state.cart[mon_id] -= 1
                            st.rerun()
                    with c2:
                        # Căn giữa số lượng
                        st.markdown(f"<div style='text-align: center; margin-top: 10px;'><h4>{qty}</h4></div>", unsafe_allow_html=True)
                    with c3:
                        if st.button("➕", key=f"plus_{mon_id}", type="primary", use_container_width=True):
                            st.session_state.cart[mon_id] += 1
                            st.rerun()
        st.markdown("---")
        # ==========================================

        # ==========================================
        # FORM THÔNG TIN GIAO HÀNG & CHỐT ĐƠN
        # ==========================================
        st.header("👤 Thông tin giao hàng")
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            # Thêm các 'key' vào đây
            ten_khach = st.text_input("Tên khách hàng (*)", placeholder="Ví dụ: Anh Tuấn", key="input_ten")
            sdt = st.text_input("Số điện thoại (*)", placeholder="Ví dụ: 0905... (10 số)", key="input_sdt")
            so_nha = st.text_input("Số nhà + Tên đường (*)", placeholder="Ví dụ: K123/45 Lê Duẩn", key="input_sonha")
            phuong = st.text_input("Phường (*)", placeholder="Ví dụ: Thạch Thang", key="input_phuong")
            # ... (các mục khác) ...
            note = st.text_area("Ghi chú (Note)", key="input_note")
            
        with col_form2:
            ngay_giao = st.date_input("Ngày giao hàng (*)", value=date.today())
            # Giờ giao hàng
            gio_giao = st.time_input("Giờ giao hàng (*)", value=time(11, 30))
            phi_ship_manual = st.number_input("Phí ship thủ công (Nếu trên 7km hoặc cần sửa)", min_value=0, value=0, step=5000, help="Điền số tiền nếu cần ghi đè phí ship tự động")
            st.markdown("---")
            # Logic phí ship sau khi điền Phường (Defaults Đà Nẵng)
            final_address = f"{so_nha}, {phuong}, Đà Nẵng"
            phi_ship = 0
            
            if phuong.strip() and so_nha.strip():
                dist = get_distance_km(final_address)
                # Logic phí ship cũ
                if phi_ship_manual > 0:
                    phi_ship = phi_ship_manual
                    st.info(f"🚚 **Phí ship thủ công:** {phi_ship:,.0f} đ")
                elif dist != -1.0:
                    if dist <= 3: phi_ship = 0
                    elif dist <= 4: phi_ship = 5000
                    elif dist <= 5: phi_ship = 10000
                    elif dist <= 6: phi_ship = 15000
                    elif dist <= 7: phi_ship = 20000
                    else: phi_ship = 25000 # Trên 7km mặc định
                    st.success(f"🚚 **Phí ship tự tính:** {phi_ship:,.0f} đ (Cách {dist:.1f}km)")
            else:
                phi_ship = 0
                st.warning("⚠️ **Không xác định được khoảng cách. Phí ship đang là 0đ.**")

            tra_chai = st.number_input("Số set trả chai (Bottle return)", min_value=0, step=1, value=0, help="Số lượng chai (bù/hoàn) từ các đơn trước...")
            
            st.markdown("---")
            
            # --- TÍNH TOÁN TIỀN TỔNG QUAN ---
            total_items_money = 0
            total_items_qty = 0
            
            # Duyệt giỏ hàng để tính tổng tiền món ăn
            for mon_id, sl in st.session_state.cart.items():
                if sl > 0:
                    mon_row = df_menu[df_menu['id'] == mon_id].iloc[0]
                    total_items_money += pd.to_numeric(mon_row['gia_tien']) * sl
                    total_items_qty += sl
            
            discount_chai = int(tra_chai) * 9000
            total_to_thu = total_items_money + phi_ship - discount_chai
            if total_to_thu < 0: total_to_thu = 0 # Tránh trường hợp trừ chai ra tiền âm
            
            if total_items_qty > 0:
                st.markdown(f"#### Chi tiết tính tiền (Order detail):")
                st.write(f"- Tổng tiền món: {total_items_money:,.0f} đ")
                st.write(f"- Phí ship: {phi_ship:,.0f} đ")
                st.write(f"- Trừ tiền trả chai: - {discount_chai:,.0f} đ")
                st.error(f"💰 **TỔNG THU: {total_to_thu:,.0f} đ**")
            
            st.markdown("---")
            
            # --- CHỐT ĐƠN (Ghi đơn hàng Supabase) ---
            if st.button("💾 ĐẶT HÀNG NGAY", type="primary", use_container_width=True):
                # 1. Validation form & giỏ hàng
                if not ten_khach.strip(): st.error("Vui lòng điền 'Tên khách hàng'."); st.stop()
                if not sdt.strip(): st.error("Vui lòng điền 'Số điện thoại'."); st.stop()
                if not so_nha.strip(): st.error("Vui lòng điền 'Số nhà + Tên đường'."); st.stop()
                if not phuong.strip(): st.error("Vui lòng điền 'Phường'."); st.stop()
                if not ngay_giao: st.error("Vui lòng chọn 'Ngày giao hàng'."); st.stop()
                if not gio_giao: st.error("Vui lòng chọn 'Giờ giao hàng'."); st.stop()
                if total_items_qty == 0: st.error("Giỏ hàng đang trống, vui lòng chọn ít nhất một món."); st.stop()
                
                # 2. Tạo JSON Giỏ hàng (danh sách nhiều món đồ uống)
                order_items_json = []
                for mon_id, sl in st.session_state.cart.items():
                    if sl > 0:
                        mon_row = df_menu[df_menu['id'] == mon_id].iloc[0]
                        order_items_json.append({"ten_mon": mon_row['ten_mon'], "so_luong": int(sl)})
                
                # 3. Tạo Order Object
                # Cấu trúc bảng orders của Supabase: ten_khach, sdt, so_nha_duong, phuong, thanh_pho, ngay_giao, gio_giao, note, phi_ship, tra_chai, chi_tiet_don, tong_tien, trang_thai
                order_data = {
                    "ten_khach": ten_khach.strip(),
                    "sdt": sdt.strip(),
                    "so_nha_duong": so_nha.strip(),
                    "phuong": phuong.strip(),
                    "thanh_pho": "Đà Nẵng",
                    "ngay_giao": ngay_giao.strftime('%Y-%m-%d'),
                    "gio_giao": gio_giao.strftime('%H:%M:%S'),
                    "note": note.strip(),
                    "phi_ship": int(phi_ship),
                    "tra_chai": int(tra_chai),
                    "chi_tiet_don": order_items_json, # Format JSON cho cột jsonb của Supabase
                    "tong_tien": int(total_to_thu),
                    "trang_thai": "Chờ xử lý"
                }
                
                # 4. Ghi Supabase
                try:
                    with st.spinner("Đang gửi đơn hàng của bạn..."):
                        # Chỉ cần dùng đối tượng supabase có sẵn trong utils.py
                        supabase.table("orders").insert(order_data).execute()
                        st.success("🎉 Đã đặt hàng thành công! Vui lòng chờ shop xác nhận đơn hàng nhé.")
                    # Xóa cache/giỏ hàng để reset trang
                    st.cache_data.clear()
                    if "df_orders" in st.session_state: del st.session_state["df_orders"]
                    if "cart" in st.session_state: del st.session_state.cart
                    for key in ["input_ten", "input_sdt", "input_sonha", "input_phuong", "input_note"]:
                        if key in st.session_state:
                            del st.session_state[key]
                            st.query_params["refresh"] = "true"
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi gửi đơn hàng: {e}")

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")
