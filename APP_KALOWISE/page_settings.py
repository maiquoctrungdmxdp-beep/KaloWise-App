import streamlit as st
import pandas as pd
from utils import load_prices, supabase

def render():
    st.title("⚙️ CÀI ĐẶT THỰC ĐƠN & BẢNG GIÁ")
    st.info("💡 Thêm, sửa, xóa các món trong thực đơn. Bỏ tick 'Đang Bán' nếu hôm nay quán tạm hết món đó.")
    try:
        # 1. Load dữ liệu từ Supabase
        if "df_prices" not in st.session_state:
            with st.spinner("Đang tải thực đơn..."):
                st.session_state["df_prices"] = load_prices()
                
        df = st.session_state["df_prices"]
        
        # Nếu bảng trống, tạo cấu trúc chuẩn
        if df.empty:
            df = pd.DataFrame(columns=['id', 'created_at', 'ten_mon', 'gia_tien', 'dang_ban'])
            
        # Lọc ra các cột cần cho việc chỉnh sửa
        edit_cols = ['id', 'ten_mon', 'gia_tien', 'dang_ban']
        
        # Đảm bảo đủ cột nếu database mới tinh
        for col in edit_cols:
            if col not in df.columns:
                if col == 'dang_ban': df[col] = True
                else: df[col] = None

        df_edit = df[edit_cols].copy()
        
        # 2. Giao diện bảng thông minh (Ẩn cột ID, làm đẹp các cột khác)
        edited_df = st.data_editor(
            df_edit, 
            use_container_width=True, 
            num_rows="dynamic",
            key="menu_editor",
            column_config={
                "id": None, # Ẩn cột id không cho sửa
                "ten_mon": st.column_config.TextColumn("Tên Món / Set", required=True),
                "gia_tien": st.column_config.NumberColumn("Giá Tiền (VNĐ)", required=True, min_value=0, step=1000),
                "dang_ban": st.column_config.CheckboxColumn("Đang Bán", default=True)
            }
        )
        
        # 3. Xử lý logic lưu dữ liệu xuống Database (CRUD)
        if st.button("💾 Lưu Cập Nhật Lên Supabase", type="primary"):
            with st.spinner('Đang đồng bộ thực đơn...'):
                
                # Bắt các sự kiện thay đổi từ bảng editor
                changes = st.session_state["menu_editor"]
                added = changes.get("added_rows", [])
                edited = changes.get("edited_rows", {})
                deleted = changes.get("deleted_rows", [])
                
                try:
                    # XÓA MÓN
                    if deleted:
                        # Streamlit trả về list các số thứ tự (index) bị xóa, ta phải sắp xếp giảm dần 
                        # để tránh lỗi lệch dòng
                        for idx in sorted(deleted, reverse=True):
                            row_id = df_edit.iloc[idx]['id']
                            if pd.notna(row_id):
                                supabase.table("menu").delete().eq("id", int(row_id)).execute()
                    
                    # SỬA MÓN
                    if edited:
                        for idx_str, updates in edited.items():
                            idx = int(idx_str)
                            row_id = df_edit.iloc[idx]['id']
                            if pd.notna(row_id):
                                supabase.table("menu").update(updates).eq("id", int(row_id)).execute()
                                
                    # THÊM MÓN MỚI
                    if added:
                        for row in added:
                            new_item = {
                                "ten_mon": row.get("ten_mon", ""),
                                "gia_tien": int(row.get("gia_tien", 0)),
                                "dang_ban": row.get("dang_ban", True)
                            }
                            # Đẩy thẳng món mới lên DB, cột id và created_at sẽ tự động sinh ra
                            supabase.table("menu").insert(new_item).execute()
                            
                    st.success("Đã đồng bộ thực đơn thành công!")
                    
                    # Xóa bộ nhớ đệm và tải lại trang để thấy dữ liệu mới
                    st.cache_data.clear()
                    if "df_prices" in st.session_state:
                        del st.session_state["df_prices"]
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Lỗi khi cập nhật Database: {e}")
                    
    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")