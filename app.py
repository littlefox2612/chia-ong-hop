import streamlit as st
import pandas as pd

def solve_nesting_limited(segments_list, stock_length, blade_width, max_types, mode):
    all_segments = []
    for length, qty in segments_list:
        all_segments.extend([length] * qty)

    if mode == "Tối ưu vật tư":
        all_segments.sort(reverse=True)
    else:
        all_segments.sort()

    stocks = [] 
    for seg in all_segments:
        placed = False
        for stock in stocks:
            used_space = sum(stock) + (len(stock) * blade_width)
            current_types = set(stock)
            is_new_type = seg not in current_types
            
            if (stock_length - used_space >= seg):
                if not is_new_type or (len(current_types) < max_types):
                    stock.append(seg)
                    placed = True
                    break
        if not placed:
            stocks.append([seg])
    return stocks

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Hệ thống Chia Phôi", layout="wide")

# Sử dụng CSS để làm bảng trong sidebar rộng hơn một chút nếu cần
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            min-width: 400px;
            max-width: 450px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ Hệ Thống Chia Cắt Vật Tư")

# Khởi tạo dữ liệu mẫu
if 'df_data' not in st.session_state:
    st.session_state.df_data = pd.DataFrame([
        {"Chọn": True, "Chiều dài (mm)": 2020, "Số lượng": 33},
        {"Chọn": True, "Chiều dài (mm)": 1630, "Số lượng": 42},
        
    ])

# --- THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Cấu hình phôi")
    L_stock = st.number_input("Chiều dài cây phôi (mm)", value=6000)
    blade = st.number_input("Mạch cắt (mm)", value=3)
    
    st.divider()
    st.header("🎯 Giới hạn sản xuất")
    max_types = st.slider("Số loại kích thước tối đa/cây", 1, 5, 3)
    mode = st.selectbox("Thứ tự ưu tiên", ["Tối ưu vật tư", "Tối ưu quy trình (Làm dưỡng)"])
    
    st.divider()
    # ĐƯA BẢNG NHẬP LIỆU VÀO ĐÂY
    st.header("📋 Danh sách kích thước")
    edited_df = st.data_editor(
        st.session_state.df_data, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "Chọn": st.column_config.CheckboxColumn(width="small"),
            "Chiều dài (mm)": st.column_config.NumberColumn(width="medium"),
            "Số lượng": st.column_config.NumberColumn(width="small"),
        }
    )
    st.session_state.df_data = edited_df

    st.divider()
    # Nút bấm cũng đưa vào sidebar để tiết kiệm diện tích
    run_button = st.button("🚀 BẮT ĐẦU CHIA PHÔI", use_container_width=True, type="primary")

# --- KHU VỰC HIỂN THỊ KẾT QUẢ (CHÍNH) ---
if run_button:
    selected_data = edited_df[edited_df["Chọn"] == True]
    
    if selected_data.empty:
        st.error("Vui lòng nhập và tích chọn kích thước ở thanh bên trái!")
    else:
        segments_to_process = list(zip(selected_data["Chiều dài (mm)"], selected_data["Số lượng"]))
        results = solve_nesting_limited(segments_to_process, L_stock, blade, max_types, mode)
        
        # Thống kê nhanh
        total_used = len(results) * L_stock
        total_cut = sum([sum(s) for s in results])
        eff = (total_cut / total_used) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng phôi dùng", f"{len(results)} cây")
        c2.metric("Hiệu suất", f"{eff:.2f}%")
        c3.metric("Số loại tối đa/cây", f"{max_types} loại")

        st.divider()
        
        # Hiển thị sơ đồ
        schemes = {}
        for s in results:
            s_tuple = tuple(s)
            schemes[s_tuple] = schemes.get(s_tuple, 0) + 1

        for scheme, count in schemes.items():
            unique_in_scheme = len(set(scheme))
            st.write(f"**{L_stock} x {count} cây** (Chứa {unique_in_scheme} loại kích thước)")
            
            bar_html = f'<div style="display: flex; width: 100%; border: 2px solid #444; height: 50px; background: #262730; border-radius: 5px; overflow: hidden; margin-bottom: 2px;">'
            marks_html = '<div style="display: flex; width: 100%; position: relative; height: 30px; font-size: 12px; font-family: monospace; margin-bottom: 20px;">'
            
            current_mark = 0
            color_map = {length: f"hsl({(i * 137) % 360}, 65%, 45%)" for i, length in enumerate(set(scheme))}
            
            for length in scheme:
                width_pct = (length / L_stock) * 100
                bg_color = color_map[length]
                bar_html += f'<div style="width: {width_pct}%; background: {bg_color}; border-right: 1px solid #fff; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 15px;">{length}</div>'
                
                current_mark += length
                mark_pos = (current_mark / L_stock) * 100
                marks_html += f'<div style="position: absolute; left: {mark_pos}%; transform: translateX(-50%); border-left: 2px solid #ff4b4b; height: 12px; padding-top: 5px; font-weight: bold; color: #ff4b4b;">{current_mark}</div>'
                current_mark += blade

            bar_html += '</div>'
            marks_html += '</div>'
            
            st.markdown(bar_html, unsafe_allow_html=True)
            st.markdown(marks_html, unsafe_allow_html=True)
else:
    # Thông báo khi mới mở app
    st.info("👈 Hãy nhập danh sách kích thước và nhấn nút 'Bắt đầu' ở thanh bên trái để xem kết quả.")