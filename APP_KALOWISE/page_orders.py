import streamlit as st
import pandas as pd
import urllib.parse
import json
from streamlit_autorefresh import st_autorefresh
from utils import load_orders, load_prices, get_distance_km, supabase

def render():
    st.title("📦 DANH SÁCH ĐƠN HÀNG")
    st_autorefresh(interval=300000, limit=None, key="order_refresh")
        
    try:
        # Load dữ liệu từ Supabase
        if "df_orders" not in st.session_state:
            with st.spinner("Đang tải lại dữ liệu..."):
                st.session_state["df_orders"] = load_orders()
        df = st.session_state["df_orders"]
        
        if df.empty:
            st.info("Chưa có đơn hàng nào hiện tại.")
            return

        # Kiểm tra xem cấu trúc bảng mới đã có cột trang_thai chưa
        if 'trang_thai' not in df.columns:
            st.cache_data.clear()
            if "df_orders" in st.session_state:
                del st.session_state["df_orders"]
            st.rerun()
            return

        # Lọc các đơn chưa hoàn thành
        active_indices = df[df['trang_thai'] != 'Đã xong'].index.tolist()
        
        if not active_indices:
            st.info("Hiện không có đơn hàng nào cần xử lý.")
        else:
            cols = st.columns(3)
            # Duyệt qua các đơn hàng
            for i, index in enumerate(active_indices):
                row = df.loc[index] 
                col = cols[i % 3]
                
                # --- Map biến với dữ liệu ---
                order_id = row['id']
                ten_khach = str(row.get('ten_khach', 'Khách'))
                sdt = str(row.get('sdt', ''))
                so_nha = str(row.get('so_nha_duong', '')).strip()
                phuong = str(row.get('phuong', '')).strip()
                thanh_pho = str(row.get('thanh_pho', 'Đà Nẵng')).strip()
                full_address = f"{so_nha}, {phuong}, {thanh_pho}"
                gio_giao = str(row.get('gio_giao', ''))
                note = str(row.get('note', ''))
                
                phi_ship = pd.to_numeric(row.get('phi_ship', 0), errors='coerce')
                if pd.isna(phi_ship): phi_ship = 0
                
                tong_tien = pd.to_numeric(row.get('tong_tien', 0), errors='coerce')
                if pd.isna(tong_tien): tong_tien = 0

                tra_chai = pd.to_numeric(row.get('tra_chai', 0), errors='coerce')
                if pd.isna(tra_chai): tra_chai = 0

                chi_tiet = row.get('chi_tiet_don')
                if isinstance(chi_tiet, str):
                    try: chi_tiet = json.loads(chi_tiet)
                    except: chi_tiet = []
                elif not isinstance(chi_tiet, list):
                    chi_tiet = []

                encoded_address = urllib.parse.quote(full_address)
                map_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_address}&travelmode=driving"
                
                # ==========================================
                # HIỂN THỊ GIAO DIỆN THẺ (ORDER CARD)
                # ==========================================
                with col.container(border=True):
                    
                    # 1. Tên khách (Căn giữa, font chữ lớn, màu xanh thanh lịch)
                    st.markdown(f"<h3 style='text-align: center; color: #2c3e50; margin-bottom: 5px; font-weight: 800;'>📍 {ten_khach}</h3>", unsafe_allow_html=True)
                    
                    # 2. Số điện thoại (Biến thành Nút bấm Call, căn giữa)
                    if sdt and sdt != 'nan':
                        st.markdown(f"""
                        <div style="text-align: center; margin-bottom: 20px;">
                            <a href="tel:{sdt}" style="background-color: #e3f2fd; color: #1565c0; padding: 6px 20px; border-radius: 20px; text-decoration: none; font-weight: 600; display: inline-block; border: 1px solid #90caf9; font-size: 15px; transition: 0.3s; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                                📞 Gọi ngay: {sdt}
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
                        
                    # 3. Thông tin chi tiết (Giữ nguyên lề trái để dễ đọc)
                    if gio_giao and gio_giao != 'nan':
                        st.write(f"⏰ **Giờ giao:** {gio_giao}")
                    
                    st.write("📦 **Sản phẩm:**")
                    if chi_tiet:
                        for item in chi_tiet:
                            st.markdown(f"<div style='margin-left: 20px; margin-bottom: 6px;'>▪️ {item.get('ten_mon', '')} <b>(SL: {item.get('so_luong', 1)})</b></div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='margin-left: 20px;'>- (Chưa có chi tiết)</div>", unsafe_allow_html=True)
                        
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.write(f"🏠 **Địa chỉ:** {full_address}")
                    
                    if tra_chai > 0:
                        st.write(f"🍾 **Trả chai:** {int(tra_chai)} set *(Đã trừ vào tổng)*")
                        
                    st.write(f"🚚 **Phí ship:** {int(phi_ship):,.0f} đ")
                    
                    # 4. Block Ghi chú (Thiết kế nền vàng nhạt cảnh báo)
                    if note and note != 'nan' and note.strip() != "":
                        st.markdown(f"""
                        <div style="background-color: #fffde7; padding: 12px; border-radius: 8px; border-left: 5px solid #ffca28; margin-top: 15px; margin-bottom: 5px; font-size: 14.5px; color: #5d4037;">
                            📝 <b>Ghi chú:</b> {note}
                        </div>
                        """, unsafe_allow_html=True)
                        
                    # 5. Box Tiền Cần Thu (Căn giữa, to, rõ, nền hồng nhạt)
                    st.markdown(f"""
                    <div style="background-color: #ffebee; padding: 15px; border-radius: 10px; text-align: center; margin-top: 20px; margin-bottom: 15px; border: 1.5px solid #ffcdd2;">
                        <h4 style="color: #c62828; margin: 0; font-weight: 800;">💰 CẦN THU: {int(tong_tien):,.0f} đ</h4>
                    </div>
                    """, unsafe_allow_html=True)  
                    
                    # 6. Cụm nút bấm tương tác gốc của Streamlit
                    st.link_button("🗺️ Chỉ đường trên Maps", url=map_url, use_container_width=True)
                    
                    if st.button("✅ Hoàn thành đơn", key=f"done_{order_id}", type="primary", use_container_width=True):
                        try:
                            supabase.table("orders").update({"trang_thai": "Đã xong"}).eq("id", order_id).execute()
                            st.session_state["df_orders"].at[index, 'trang_thai'] = 'Đã xong'
                            st.success("Đã hoàn thành!")
                            st.rerun() 
                        except Exception as e:
                            st.error(f"Lỗi khi cập nhật: {e}")
                                
        # --- Bảng chỉnh sửa dành cho Admin ---
        st.markdown("---")
        with st.expander("📝 BẢNG SỬA ĐƠN & QUẢN TRỊ", expanded=False):
            st.info("💡 **Mẹo:** Bảng này dùng để sửa sai thông tin hoặc cập nhật phí ship thủ công.")
            edit_cols = [c for c in df.columns if c not in ['chi_tiet_don', 'created_at']]
            df_edit = df[edit_cols].copy()
            st.data_editor(df_edit, use_container_width=True, num_rows="dynamic", key="order_editor")
            
            if st.button("💾 Lưu Thay Đổi Lên Database", type="primary"):
                with st.spinner('Đang đồng bộ...'):
                    try:
                        changes = st.session_state["order_editor"]
                        edited_rows = changes.get("edited_rows", {})
                        if edited_rows:
                            for row_idx_str, updates in edited_rows.items():
                                row_idx = int(row_idx_str)
                                row_id = int(df_edit.iloc[row_idx]['id'])
                                supabase.table("orders").update(updates).eq("id", row_id).execute()
                            
                            st.success("Đã đồng bộ cập nhật thành công!")
                            st.cache_data.clear()
                            del st.session_state["df_orders"]
                            st.rerun()
                        else:
                            st.info("Không có thay đổi nào cần lưu.")
                    except Exception as e:
                        st.error(f"Lỗi khi lưu: {e}")
                        
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")