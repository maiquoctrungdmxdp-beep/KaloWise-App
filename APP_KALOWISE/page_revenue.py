import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_orders

def render():
    st.title("💰 THỐNG KÊ DOANH THU")
    try:
        # 1. Load dữ liệu từ Supabase (thông qua session_state)
        if "df_orders" not in st.session_state:
            with st.spinner("Đang tải lại dữ liệu..."):
                st.session_state["df_orders"] = load_orders()
                
        df_full = st.session_state["df_orders"]
        
        # Kiểm tra dữ liệu rỗng hoặc chưa có cột trạng thái
        if df_full.empty or 'trang_thai' not in df_full.columns:
            st.info("Chưa có đơn hàng nào để thống kê.")
            return
            
        # Lọc ra những đơn hàng "Đã xong"
        df_done = df_full[df_full['trang_thai'] == 'Đã xong'].copy()
        
        if df_done.empty:
            st.info("Chưa có đơn hàng nào hoàn thành để thống kê.")
            return

        # 2. Xử lý kiểu dữ liệu (Ép về số để cộng trừ cho chuẩn)
        df_done['tong_tien'] = pd.to_numeric(df_done['tong_tien'], errors='coerce').fillna(0)
        df_done['phi_ship'] = pd.to_numeric(df_done['phi_ship'], errors='coerce').fillna(0)
        df_done['tra_chai'] = pd.to_numeric(df_done['tra_chai'], errors='coerce').fillna(0)
        
        # 3. Chuẩn bị cột Ngày và Tháng để làm bộ lọc (Dựa vào created_at của Supabase)
        df_done['Ngày thực tế'] = pd.to_datetime(df_done['created_at']).dt.date
        df_done['Tháng/Năm'] = pd.to_datetime(df_done['created_at']).dt.strftime('%m/%Y')
        
        # ==========================================
        # BỘ LỌC DỮ LIỆU (DROP BOX CHỌN NGÀY THÁNG)
        # ==========================================
        st.markdown("### 🔍 Bộ lọc doanh thu")
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            loai_loc = st.selectbox("Cách lọc dữ liệu:", ["Tất cả", "Theo Tháng/Năm", "Theo Ngày cụ thể"])
            
        with col_filter2:
            if loai_loc == "Theo Tháng/Năm":
                danh_sach_thang = df_done['Tháng/Năm'].dropna().unique().tolist()
                if danh_sach_thang:
                    thang_chon = st.selectbox("📅 Chọn Tháng:", danh_sach_thang)
                    df_done = df_done[df_done['Tháng/Năm'] == thang_chon]
                else:
                    st.warning("Không có dữ liệu thời gian.")
                    
            elif loai_loc == "Theo Ngày cụ thể":
                ngay_chon = st.date_input("📅 Chọn ngày (hoặc khoảng ngày):", [])
                if len(ngay_chon) == 2:
                    start_date, end_date = ngay_chon
                    df_done = df_done[(df_done['Ngày thực tế'] >= start_date) & (df_done['Ngày thực tế'] <= end_date)]
                elif len(ngay_chon) == 1:
                    df_done = df_done[df_done['Ngày thực tế'] == ngay_chon[0]]
        st.markdown("---")
        # ==========================================

        # Tính tổng quan DỰA TRÊN DỮ LIỆU ĐÃ LỌC
        tong_doanh_thu = df_done['tong_tien'].sum()
        tong_don_hang = len(df_done)
        
        # --- HIỂN THỊ TỔNG QUAN ---
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tổng Số Đơn Hàng", f"{tong_don_hang} đơn")
        with col2:
            st.metric("Tổng Doanh Thu (Gồm Ship)", f"{tong_doanh_thu:,.0f} VNĐ")
        
        st.markdown("---")
        
        # --- THỐNG KÊ THEO NGÀY ---
        st.markdown("### 📅 Thống kê doanh thu theo ngày")
        
        if not df_done.empty and not df_done['Ngày thực tế'].isna().all():
            doanh_thu_ngay = df_done.groupby('Ngày thực tế').agg(
                Số_đơn_hàng=('id', 'count'),
                Tổng_doanh_thu=('tong_tien', 'sum')
            ).reset_index()
            
            doanh_thu_ngay = doanh_thu_ngay.sort_values(by='Ngày thực tế', ascending=False)
            doanh_thu_ngay['Ngày'] = pd.to_datetime(doanh_thu_ngay['Ngày thực tế']).dt.strftime('%d/%m/%Y')
            
            # --- BIỂU ĐỒ PLOTLY ---
            fig = px.bar(
                doanh_thu_ngay, 
                x='Ngày', 
                y='Tổng_doanh_thu',
                text='Tổng_doanh_thu', 
                color_discrete_sequence=['#FF4B4B'] 
            )
            
            fig.update_traces(
                texttemplate='%{text:,.0f} đ', 
                textposition='outside',       
                width=0.4 if len(doanh_thu_ngay) == 1 else None 
            )
            
            fig.update_layout(
                xaxis_title="", 
                yaxis_title="Doanh Thu (VNĐ)",
                plot_bgcolor="rgba(0,0,0,0)", 
                margin=dict(t=30, b=20, l=0, r=0) 
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Bảng hiển thị tóm tắt theo ngày
            st.dataframe(
                doanh_thu_ngay[['Ngày', 'Số_đơn_hàng', 'Tổng_doanh_thu']].rename(
                    columns={'Số_đơn_hàng': 'Số đơn', 'Tổng_doanh_thu': 'Doanh Thu (VNĐ)'}
                ),
                use_container_width=True
            )
        else:
            st.info("Chưa có đủ dữ liệu để hiển thị biểu đồ trong khoảng thời gian này.")
            
        st.markdown("---")
        
        # --- CHI TIẾT TỪNG ĐƠN HÀNG ---
        st.markdown("### 📊 Chi tiết doanh thu từng đơn")
        
        # Đổi tên cột cho đẹp trước khi hiển thị
        df_display = df_done[['created_at', 'ten_khach', 'phi_ship', 'tra_chai', 'tong_tien']].copy()
        df_display.rename(columns={
            'created_at': 'Thời gian đặt',
            'ten_khach': 'Tên khách hàng',
            'phi_ship': 'Phí Ship',
            'tra_chai': 'Số set trả chai',
            'tong_tien': 'Tổng thu'
        }, inplace=True)
        
        # Format lại thời gian cho dễ nhìn
        df_display['Thời gian đặt'] = pd.to_datetime(df_display['Thời gian đặt']).dt.strftime('%H:%M %d/%m/%Y')
        
        st.dataframe(df_display, use_container_width=True)
        
        # --- XUẤT FILE EXCEL (CSV) NATIVE STREAMLIT ---
        st.markdown("---")
        st.markdown("### 📥 Tải dữ liệu về máy")
        
        # Chuyển dataframe thành định dạng CSV
        csv = df_display.to_csv(index=False).encode('utf-8-sig') # Dùng utf-8-sig để Excel đọc tiếng Việt không bị lỗi font
        
        st.download_button(
            label="⬇️ Tải Báo Cáo Doanh Thu (CSV)",
            data=csv,
            file_name='Bao_Cao_Doanh_Thu.csv',
            mime='text/csv',
            type="primary"
        )
                
    except Exception as e:
        st.error(f"Lỗi khi thống kê: {e}")