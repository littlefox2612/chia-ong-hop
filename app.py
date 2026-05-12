import streamlit as st
import pandas as pd

# --- CẤU HÌNH ---
st.set_page_config(page_title="Hệ thống Chia Phôi", layout="wide")

if 'df_data' not in st.session_state:
    st.session_state.df_data = pd.DataFrame(columns=["Xóa", "Chiều dài (mm)", "Số lượng"])
if 'history' not in st.session_state:
    st.session_state.history = []

# --- THANH BÊN (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Cấu hình phôi")
    L_stock = st.number_input("Chiều dài cây phôi (mm)", value=6000)
    blade = st.number_input("Mạch cắt (mm)", value=3)
    
    st.divider()
    st.header("🎯 Giới hạn sản xuất")
    max_types = st.slider("Số loại kích thước tối đa/cây", 1, 5, 2)
    
    st.divider()
    st.header("➕ Nhập kích thước nhanh")
    
    # SỬA ĐỔI TẠI ĐÂY: Dùng text_input để nhận giá trị gõ phím nhạy hơn
    with st.form("input_form", clear_on_submit=True):
        col_l, col_q = st.columns(2)
        # Nhập dạng chữ nhưng sẽ ép kiểu sang số sau
        raw_l = col_l.text_input("Chiều dài", value="", placeholder="Ví dụ: 2020")
        raw_q = col_q.text_input("Số lượng", value="1", placeholder="Ví dụ: 10")
        
        submit_add = st.form_submit_button("Thêm vào danh sách (Enter)", use_container_width=True)
        
        if submit_add:
            try:
                # Ép kiểu dữ liệu và kiểm tra hợp lệ
                val_l = int(raw_l)
                val_q = int(raw_q)
                if val_l > 0 and val_q > 0:
                    new_row = pd.DataFrame([{"Xóa": False, "Chiều dài (mm)": val_l, "Số lượng": val_q}])
                    st.session_state.df_data = pd.concat([st.session_state.df_data, new_row], ignore_index=True)
                    st.rerun()
                else:
                    st.error("Số phải lớn hơn 0")
            except:
                st.error("Vui lòng chỉ nhập số!")

    st.divider()
    st.header("📋 Danh sách đã nhập")
    
    # Bảng hiển thị đã ẩn cột Index (Số 0, 1, 2... None)
    edited_df = st.data_editor(
        st.session_state.df_data, 
        num_rows="dynamic", 
        use_container_width=True,
        key="data_editor_key",
        column_config={
            "Xóa": st.column_config.CheckboxColumn(width="small"),
            "Chiều dài (mm)": st.column_config.NumberColumn(format="%d"),
            "Số lượng": st.column_config.NumberColumn(format="%d"),
        },
        hide_index=True, # Ẩn cột thừa theo yêu cầu của bạn
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🗑️ Xóa", use_container_width=True):
            st.session_state.history.append(st.session_state.df_data.copy())
            st.session_state.df_data = edited_df[edited_df["Xóa"] == False].reset_index(drop=True)
            st.rerun()
    with col_btn2:
        if st.button("⏪ Undo", use_container_width=True):
            if len(st.session_state.history) > 0:
                st.session_state.df_data = st.session_state.history.pop()
                st.rerun()

    st.divider()
    run_button = st.button("🚀 BẮT ĐẦU CHIA PHÔI", use_container_width=True, type="primary")

st.session_state.df_data = edited_df

# --- HÀM XỬ LÝ CHIA PHÔI ---
def solve_nesting_limited(segments_list, stock_length, blade_width, max_types):
    all_segments = []
    for length, qty in segments_list:
        all_segments.extend([length] * qty)
    all_segments.sort(reverse=True)
    stocks = [] 
    for seg in all_segments:
        placed = False
        for stock in stocks:
            used_space = sum(stock) + (len(stock) * blade_width)
            current_types = set(stock)
            if (stock_length - used_space >= seg):
                if (seg in current_types) or (len(current_types) < max_types):
                    stock.append(seg)
                    placed = True
                    break
        if not placed: stocks.append([seg])
    return stocks

# --- HIỂN THỊ KẾT QUẢ ---
if run_button:
    valid_data = edited_df.dropna(subset=["Chiều dài (mm)", "Số lượng"])
    if valid_data.empty:
        st.error("Danh sách trống!")
    else:
        segments_to_process = list(zip(valid_data["Chiều dài (mm)"].astype(int), valid_data["Số lượng"].astype(int)))
        results = solve_nesting_limited(segments_to_process, L_stock, blade, max_types)
        
        total_used = len(results)
        total_cut = sum([sum(s) for s in results])
        total_waste = (total_used * L_stock) - total_cut
        eff = (total_cut / (total_used * L_stock)) * 100
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng phôi dùng", f"{total_used} cây")
        c2.metric("Hiệu suất", f"{eff:.2f}%")
        c3.metric("Phế phẩm (%)", f"{100-eff:.2f}%")
        c4.metric("Tổng Đề-cê", f"{total_waste:,} mm")

        st.divider()
        schemes = {}
        for s in results:
            s_tuple = tuple(s)
            schemes[s_tuple] = schemes.get(s_tuple, 0) + 1

        for scheme, count in schemes.items():
            single_waste = L_stock - (sum(scheme) + (len(scheme) - 1) * blade)
            st.write(f"**{L_stock} x {count} cây** (Dư: {single_waste}mm)")
            
            bar_html = f'<div style="display: flex; width: 100%; border: 2px solid #444; height: 50px; background: #262730; border-radius: 5px; overflow: hidden; margin-bottom: 2px;">'
            marks_html = '<div style="display: flex; width: 100%; position: relative; height: 30px; font-size: 12px; font-family: monospace; margin-bottom: 20px;">'
            
            current_mark = 0
            color_map = {length: f"hsl({(hash(str(length)) % 360)}, 70%, 45%)" for length in set(scheme)}
            for length in scheme:
                width_pct = (length / L_stock) * 100
                bg_color = color_map[length]
                bar_html += f'<div style="width: {width_pct}%; background: {bg_color}; border-right: 1px solid #fff; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 15px;">{length}</div>'
                current_mark += length
                mark_pos = (current_mark / L_stock) * 100
                marks_html += f'<div style="position: absolute; left: {mark_pos}%; transform: translateX(-50%); border-left: 2px solid #ff4b4b; height: 12px; padding-top: 5px; font-weight: bold; color: #ff4b4b;">{current_mark}</div>'
                current_mark += blade
            st.markdown(bar_html + '</div>', unsafe_allow_html=True)
            st.markdown(marks_html + '</div>', unsafe_allow_html=True)
