import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict, Tuple

# ---------- Cấu hình trang ----------
st.set_page_config(
    page_title="Gunpla Spray Day",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Dữ liệu tỉnh/thành (lat, lon) ----------
PROVINCES: Dict[str, Tuple[float, float]] = {
    "An Giang": (10.5216, 105.1259),
    "Bà Rịa - Vũng Tàu": (10.4114, 107.1379),
    "Bạc Liêu": (9.2941, 105.7278),
    "Bắc Ninh": (21.1861, 106.0763),
    "Bến Tre": (10.2417, 106.3759),
    "Bình Dương": (10.9805, 106.6523),
    "Bình Phước": (11.7514, 106.9159),
    "Bình Thuận": (10.9778, 108.2685),
    "Cà Mau": (9.1805, 105.1505),
    "Cần Thơ": (10.0727, 105.8062),
    "Đà Nẵng": (16.0544, 108.2022),
    "Đắk Lắk": (12.6665, 108.0381),
    "Đồng Nai": (10.9989, 106.8103),
    "Đồng Tháp": (10.4938, 105.6882),
    "Gia Lai": (13.9829, 108.0121),
    "Hà Giang": (22.7669, 105.0286),
    "Hà Nam": (20.5835, 105.9223),
    "Hà Nội": (21.0285, 105.8542),
    "Hà Tĩnh": (18.3557, 105.8878),
    "Hải Dương": (20.9412, 106.3155),
    "Hải Phòng": (20.8449, 106.6881),
    "Hậu Giang": (9.7847, 105.4692),
    "Hòa Bình": (20.6861, 105.2555),
    "Hưng Yên": (20.8521, 106.0942),
    "Khánh Hòa": (12.2584, 109.1853),
    "Kiên Giang": (10.0239, 105.0152),
    "Kon Tum": (14.3493, 108.0091),
    "Lai Châu": (22.3865, 103.6103),
    "Lâm Đồng": (11.5755, 108.1429),
    "Lạng Sơn": (21.8526, 106.7619),
    "Lào Cai": (22.4856, 103.9665),
    "Long An": (10.7010, 106.4232),
    "Nam Định": (20.4386, 106.1621),
    "Nghệ An": (19.4803, 105.7019),
    "Ninh Bình": (20.2459, 105.9805),
    "Ninh Thuận": (11.6739, 108.8629),
    "Phú Thọ": (21.2689, 105.2041),
    "Phú Yên": (13.0886, 109.0929),
    "Quảng Bình": (17.4684, 106.6226),
    "Quảng Nam": (15.5178, 108.2521),
    "Quảng Ngãi": (15.1195, 108.7933),
    "Quảng Ninh": (20.9530, 107.0513),
    "Quảng Trị": (16.7689, 107.0276),
    "Sóc Trăng": (9.6025, 105.9739),
    "Sơn La": (21.3278, 103.9135),
    "Tây Ninh": (11.3199, 106.1047),
    "Thái Bình": (20.4467, 106.3426),
    "Thái Nguyên": (21.5936, 105.8460),
    "Thanh Hóa": (19.8067, 105.7801),
    "Thừa Thiên Huế": (16.4637, 107.5909),
    "Tiền Giang": (10.3764, 106.3416),
    "TP Hồ Chí Minh": (10.8231, 106.6297),
    "Trà Vinh": (9.9519, 106.3410),
    "Tuyên Quang": (21.8235, 105.2125),
    "Vĩnh Long": (10.2505, 105.9724),
    "Vĩnh Phúc": (21.3051, 105.5937),
    "Yên Bái": (21.7236, 104.8988)
}

# ---------- Dữ liệu quận/huyện (chỉ một số thành phố lớn) ----------
# Cấu trúc: province -> {district_name: (lat, lon)}
DISTRICTS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "Hà Nội": {
        "Quận Ba Đình": (21.0358, 105.8346),
        "Quận Hoàn Kiếm": (21.0285, 105.8542),
        "Quận Hai Bà Trưng": (21.0067, 105.8611),
        "Quận Đống Đa": (21.0147, 105.8245),
        "Quận Thanh Xuân": (20.9968, 105.8141),
        "Quận Cầu Giấy": (21.0285, 105.8013),
        "Quận Long Biên": (21.0477, 105.8775),
        "Quận Nam Từ Liêm": (21.0047, 105.7582),
        "Quận Bắc Từ Liêm": (21.0796, 105.7616),
        "Huyện Từ Liêm": (21.0285, 105.8013),  # cũ
    },
    "TP Hồ Chí Minh": {
        "Quận 1": (10.7766, 106.7001),
        "Quận 2": (10.7909, 106.7565),
        "Quận 3": (10.7844, 106.6859),
        "Quận 4": (10.7626, 106.7029),
        "Quận 5": (10.7545, 106.6701),
        "Quận 6": (10.7465, 106.6406),
        "Quận 7": (10.7310, 106.7175),
        "Quận 8": (10.7240, 106.6305),
        "Quận 9": (10.8484, 106.7810),
        "Quận 10": (10.7760, 106.6721),
        "Quận 11": (10.7643, 106.6500),
        "Quận 12": (10.8603, 106.6576),
        "Quận Bình Tân": (10.7540, 106.6026),
        "Quận Bình Thạnh": (10.8095, 106.7064),
        "Quận Gò Vấp": (10.8349, 106.6753),
        "Quận Phú Nhuận": (10.8004, 106.6794),
        "Quận Tân Bình": (10.8032, 106.6561),
        "Quận Tân Phú": (10.7895, 106.6276),
        "Quận Thủ Đức": (10.8571, 106.7577),
        "Huyện Bình Chánh": (10.7213, 106.6689),
        "Huyện Cần Giờ": (10.4051, 106.9725),
        "Huyện Củ Chi": (11.0144, 106.4960),
        "Huyện Hóc Môn": (10.8775, 106.5916),
        "Huyện Nhà Bè": (10.6689, 106.7428),
    },
    "Đà Nẵng": {
        "Quận Hải Châu": (16.0544, 108.2022),
        "Quận Thanh Khê": (16.0587, 108.1797),
        "Quận Sơn Trà": (16.0742, 108.2440),
        "Quận Ngũ Hành Sơn": (16.0034, 108.2647),
        "Quận Liên Chiểu": (16.0769, 108.1513),
        "Quận Cẩm Lệ": (16.0080, 108.2079),
        "Huyện Hòa Vang": (15.9842, 108.1390),
    },
    "Cần Thơ": {
        "Quận Ninh Kiều": (10.0452, 105.7869),
        "Quận Bình Thủy": (10.0706, 105.7682),
        "Quận Cái Răng": (9.9908, 105.7899),
        "Quận Ô Môn": (10.1250, 105.6228),
        "Quận Thốt Nốt": (10.2543, 105.5360),
        "Huyện Phong Điền": (9.9766, 105.6728),
        "Huyện Cờ Đỏ": (10.1060, 105.4453),
        "Huyện Vĩnh Thạnh": (10.2268, 105.4067),
        "Huyện Thới Lai": (10.0141, 105.5722),
    },
    "Hải Phòng": {
        "Quận Hồng Bàng": (20.8387, 106.6822),
        "Quận Ngô Quyền": (20.8484, 106.6914),
        "Quận Lê Chân": (20.8402, 106.6932),
        "Quận Hải An": (20.8192, 106.7319),
        "Quận Kiến An": (20.8080, 106.6355),
        "Quận Đồ Sơn": (20.7061, 106.7837),
        "Quận Dương Kinh": (20.7811, 106.7516),
        "Huyện An Dương": (20.8879, 106.6012),
        "Huyện An Lão": (20.8102, 106.5489),
        "Huyện Kiến Thụy": (20.7517, 106.6939),
        "Huyện Tiên Lãng": (20.7048, 106.5367),
        "Huyện Vĩnh Bảo": (20.7205, 106.4160),
        "Huyện Cát Hải": (20.7849, 106.9676),
        "Huyện Bạch Long Vĩ": (20.1305, 107.7239),
    }
}

# ---------- Khởi tạo session state ----------
if "province" not in st.session_state:
    st.session_state.province = "TP Hồ Chí Minh"
if "district" not in st.session_state:
    st.session_state.district = "Trung tâm"
if "lat" not in st.session_state:
    st.session_state.lat, st.session_state.lon = PROVINCES["TP Hồ Chí Minh"]

# ---------- Hàm cập nhật tọa độ ----------
def update_coordinates():
    province = st.session_state.province
    district = st.session_state.district
    if district != "Trung tâm" and province in DISTRICTS and district in DISTRICTS[province]:
        st.session_state.lat, st.session_state.lon = DISTRICTS[province][district]
    else:
        st.session_state.lat, st.session_state.lon = PROVINCES[province]

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🎨 Gunpla Spray")
    st.markdown("---")
    
    st.markdown("### 📍 Địa điểm")
    
    # Dropdown tỉnh/thành
    province_list = list(PROVINCES.keys())
    selected_province = st.selectbox(
        "Tỉnh / Thành phố",
        options=province_list,
        index=province_list.index(st.session_state.province),
        key="province_selector"
    )
    if selected_province != st.session_state.province:
        st.session_state.province = selected_province
        # Reset district về "Trung tâm"
        st.session_state.district = "Trung tâm"
        update_coordinates()
        st.rerun()
    
    # Dropdown quận/huyện (chỉ khi tỉnh có dữ liệu quận)
    district_options = ["Trung tâm"]
    if st.session_state.province in DISTRICTS:
        district_options.extend(DISTRICTS[st.session_state.province].keys())
    
    selected_district = st.selectbox(
        "Quận / Huyện (nếu có)",
        options=district_options,
        index=district_options.index(st.session_state.district) if st.session_state.district in district_options else 0,
        key="district_selector"
    )
    if selected_district != st.session_state.district:
        st.session_state.district = selected_district
        update_coordinates()
        st.rerun()
    
    st.caption(f"📍 Tọa độ: {st.session_state.lat:.5f}, {st.session_state.lon:.5f}")
    
    st.markdown("---")
    st.markdown("### ⚙️ Điều kiện sơn")
    col1, col2 = st.columns(2)
    with col1:
        temp_min = st.number_input("🌡️ Nhiệt độ min (°C)", value=18.0, step=0.5)
        hum_max = st.number_input("💧 Độ ẩm max (%)", value=65, step=1)
    with col2:
        temp_max = st.number_input("🌡️ Nhiệt độ max (°C)", value=30.0, step=0.5)
        rain_max = st.number_input("☔ Mưa max (mm/h)", value=0.2, step=0.1)
    
    if st.button("🔄 Cập nhật thời tiết", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

conditions = {
    "temp_min": temp_min,
    "temp_max": temp_max,
    "hum_max": hum_max,
    "rain_max": rain_max
}

lat = st.session_state.lat
lon = st.session_state.lon
province_display = st.session_state.province
district_display = st.session_state.district

# ---------- Custom CSS (giữ nguyên như cũ, không thay đổi) ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,600;14..32,700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0b0f1c 0%, #1a1f33 100%); background-attachment: fixed; }
    [data-testid="stSidebar"] { background: rgba(20, 25, 45, 0.8); backdrop-filter: blur(16px); border-right: 1px solid rgba(255,255,255,0.08); }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #eef4ff; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #1e2642; border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: #4d608b; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #6d85b9; }
    div[data-testid="stMetric"] { background: rgba(14, 20, 36, 0.7); backdrop-filter: blur(4px); border: 1px solid #2c3855; border-radius: 24px; padding: 1rem; box-shadow: 0 8px 16px -8px rgba(0,0,0,0.4); transition: all 0.2s; }
    div[data-testid="stMetric"]:hover { transform: translateY(-2px); border-color: #5f7bbf; box-shadow: 0 12px 20px -12px #000000cc; }
    .stButton > button { background: linear-gradient(95deg, #2e3b5e 0%, #1f2a44 100%); border: none; border-bottom: 3px solid #0f1424; color: white; font-weight: 600; border-radius: 48px; padding: 0.6rem 1.2rem; transition: all 0.2s; width: 100%; }
    .stButton > button:hover { background: linear-gradient(95deg, #3e4c73 0%, #2e3b5e 100%); transform: translateY(-2px); border-bottom-width: 4px; }
    .stButton > button:active { transform: translateY(2px); border-bottom-width: 2px; }
    .forecast-card-custom { background: rgba(14, 20, 36, 0.8); backdrop-filter: blur(8px); border-radius: 28px; padding: 1.2rem; border: 1px solid #2c3855; transition: all 0.25s ease; cursor: pointer; height: 100%; display: flex; flex-direction: column; }
    .forecast-card-custom:hover { transform: translateY(-5px); border-color: #5f7bbf; box-shadow: 0 20px 25px -12px black; }
    .suitable-chip { display: inline-block; background: #1f2a44; padding: 4px 12px; border-radius: 24px; margin: 4px 4px 0 0; font-size: 0.8rem; font-weight: 500; color: #c9dcff; border: 1px solid #3e5270; }
    .streamlit-expanderHeader { background: rgba(30, 38, 66, 0.6); border-radius: 40px; font-weight: 500; }
    .custom-title { text-align: center; background: linear-gradient(135deg, #f0e9d8, #c9d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem; font-weight: 700; margin-bottom: 0; }
    .custom-subhead { text-align: center; color: #a9b4d4; margin-bottom: 2rem; border-bottom: 1px dashed #2f3a5c; display: inline-block; padding-bottom: 0.5rem; }
    .info-chip { background: #1e2642; border-radius: 60px; padding: 12px 20px; display: inline-flex; flex-wrap: wrap; gap: 20px; justify-content: center; margin-bottom: 1.5rem; border: 1px solid #334155; }
    .info-chip-item { display: flex; align-items: center; gap: 10px; color: #cbd5e1; font-size: 0.9rem; }
    .footer-note { margin-top: 2rem; font-size: 0.75rem; color: #4d5e87; text-align: center; border-top: 1px dashed #28324e; padding-top: 1.2rem; }
    label { color: #b3c2e2 !important; }
</style>
""", unsafe_allow_html=True)

# ---------- Main UI ----------
st.markdown('<h1 class="custom-title"><i class="fas fa-spray-can-sparkles"></i> Gunpla Spray Day</h1>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center"><div class="custom-subhead">Kiểm tra thời tiết, giờ phù hợp và dự báo 3 ngày</div></div>', unsafe_allow_html=True)

# Info chips
st.markdown(f"""
<div style="display: flex; justify-content: center;">
    <div class="info-chip">
        <div class="info-chip-item"><i class="fas fa-thermometer-half"></i> <span>{temp_min}–{temp_max} °C</span></div>
        <div class="info-chip-item"><i class="fas fa-droplet"></i> <span>≤ {hum_max}%</span></div>
        <div class="info-chip-item"><i class="fas fa-cloud-rain"></i> <span>Mưa < {rain_max} mm</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- Hàm helper ----------
@st.cache_data(ttl=1800)
def fetch_weather_data(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_max,weathercode",
        "timezone": "auto",
        "forecast_days": 3
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()

def group_consecutive_hours(hour_strings: List[str]) -> List[str]:
    if not hour_strings:
        return []
    hours = sorted([int(h.split(':')[0]) for h in hour_strings])
    ranges = []
    start = hours[0]
    prev = hours[0]
    for curr in hours[1:]:
        if curr == prev + 1:
            prev = curr
        else:
            if start == prev:
                ranges.append(f"{start:02d}:00")
            else:
                ranges.append(f"{start:02d}:00-{prev:02d}:00")
            start = curr
            prev = curr
    if start == prev:
        ranges.append(f"{start:02d}:00")
    else:
        ranges.append(f"{start:02d}:00-{prev:02d}:00")
    return ranges

def is_suitable(temp, humidity, rain, temp_min, temp_max, hum_max, rain_max):
    return (temp_min <= temp <= temp_max) and (humidity <= hum_max) and (rain < rain_max)

def process_hourly_data(hourly, target_date, conditions):
    times = hourly["time"]
    temps = hourly["temperature_2m"]
    hums = hourly["relative_humidity_2m"]
    rains = hourly["precipitation"]
    rows = []
    for t, tmp, hum, rn in zip(times, temps, hums, rains):
        if t.startswith(target_date):
            suitable = is_suitable(tmp, hum, rn, conditions["temp_min"], conditions["temp_max"], conditions["hum_max"], conditions["rain_max"])
            rows.append({
                "time": t,
                "hour_label": t.split("T")[1][:5],
                "temperature": tmp,
                "humidity": hum,
                "rain": rn,
                "suitable": suitable
            })
    return pd.DataFrame(rows)

def get_suitable_ranges(df):
    suitable_hours = df[df["suitable"]]["hour_label"].tolist()
    return group_consecutive_hours(suitable_hours)

# ---------- Lấy dữ liệu thời tiết ----------
try:
    data = fetch_weather_data(lat, lon)
except Exception as e:
    st.error(f"❌ Không thể lấy dữ liệu thời tiết: {e}")
    st.stop()

current = data["current"]
hourly = data["hourly"]
daily = data["daily"]

# ---------- Thời tiết hiện tại ----------
st.subheader("🌡️ Thời tiết hiện tại")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Nhiệt độ", f"{current['temperature_2m']} °C")
with col2:
    st.metric("Độ ẩm", f"{current['relative_humidity_2m']} %")
with col3:
    st.metric("Lượng mưa", f"{current['precipitation'] or 0:.1f} mm")
with col4:
    st.metric("Tốc độ gió", f"{current['wind_speed_10m']} m/s")

temp_ok = conditions["temp_min"] <= current["temperature_2m"] <= conditions["temp_max"]
hum_ok = current["relative_humidity_2m"] <= conditions["hum_max"]
rain_ok = (current["precipitation"] or 0) < conditions["rain_max"]
all_ok = temp_ok and hum_ok and rain_ok

if all_ok:
    st.success("✅ **Hôm nay là thời điểm phù hợp để sơn Gunpla!**")
else:
    reasons = []
    if not temp_ok:
        reasons.append(f"Nhiệt độ {current['temperature_2m']}°C ngoài khoảng {temp_min}–{temp_max}°C")
    if not hum_ok:
        reasons.append(f"Độ ẩm {current['relative_humidity_2m']}% > {hum_max}%")
    if not rain_ok:
        reasons.append(f"Mưa {(current['precipitation'] or 0):.1f}mm ≥ {rain_max}mm")
    st.error(f"❌ **Không phù hợp để sơn**\n\n- " + "\n- ".join(reasons))

# ---------- Giờ phù hợp hôm nay ----------
today_str = datetime.now().strftime("%Y-%m-%d")
df_today = process_hourly_data(hourly, today_str, conditions)
today_ranges = get_suitable_ranges(df_today)

st.subheader("🕒 Giờ phù hợp hôm nay")
if today_ranges:
    cols = st.columns(min(len(today_ranges), 4))
    for i, rng in enumerate(today_ranges):
        cols[i % 4].success(f"⏰ {rng}")
    # Biểu đồ
    st.markdown("#### 📈 Xu hướng trong ngày")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_today["hour_label"], y=df_today["temperature"],
                             mode='lines+markers', name='Nhiệt độ (°C)',
                             line=dict(color='#ffb347', width=3), marker=dict(size=6)))
    fig.add_trace(go.Scatter(x=df_today["hour_label"], y=df_today["humidity"],
                             mode='lines+markers', name='Độ ẩm (%)',
                             line=dict(color='#78b6ff', width=3), marker=dict(size=6), yaxis='y2'))
    suitable_hours = df_today[df_today["suitable"]]["hour_label"].tolist()
    for sh in suitable_hours:
        fig.add_vrect(x0=sh, x1=sh, line_width=0, fillcolor="green", opacity=0.2, layer="below")
    fig.update_layout(
        title="Diễn biến nhiệt độ và độ ẩm hôm nay",
        xaxis_title="Giờ",
        yaxis_title="Nhiệt độ (°C)",
        yaxis2=dict(title="Độ ẩm (%)", overlaying='y', side='right'),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0.5)"),
        height=450,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0.2)",
        font=dict(color="#eef4ff")
    )
    fig.update_xaxes(gridcolor="#334155", tickangle=45)
    fig.update_yaxes(gridcolor="#334155")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Không có giờ nào phù hợp để sơn trong hôm nay.")

# ---------- Dự báo 3 ngày ----------
st.subheader("🗓️ Dự báo 3 ngày tới")
days = daily["time"]
forecast_data = []
for i, day_str in enumerate(days):
    day_name = datetime.strptime(day_str, "%Y-%m-%d").strftime("%a, %d/%m")
    df_day = process_hourly_data(hourly, day_str, conditions)
    ranges = get_suitable_ranges(df_day)
    forecast_data.append({
        "date": day_str,
        "day_name": day_name,
        "temp_min": daily["temperature_2m_min"][i],
        "temp_max": daily["temperature_2m_max"][i],
        "precip_sum": daily["precipitation_sum"][i],
        "hum_max": daily["relative_humidity_2m_max"][i],
        "weathercode": daily["weathercode"][i],
        "suitable_ranges": ranges,
        "df_hourly": df_day
    })

cols = st.columns(3)
for idx, fc in enumerate(forecast_data):
    with cols[idx % 3]:
        code = fc["weathercode"]
        if code == 0:
            icon = "☀️"
        elif code in [1,2,3]:
            icon = "⛅"
        elif 45 <= code <= 48:
            icon = "🌫️"
        elif 51 <= code <= 57:
            icon = "🌦️"
        elif 61 <= code <= 67 or 80 <= code <= 82:
            icon = "🌧️"
        elif 71 <= code <= 77:
            icon = "❄️"
        elif 95 <= code <= 99:
            icon = "⛈️"
        else:
            icon = "☁️"
        
        st.markdown(f"""
        <div class="forecast-card-custom">
            <h3 style="text-align:center; margin:0">{fc['day_name']} {icon}</h3>
            <p style="text-align:center; margin:0.5rem 0">
                🌡️ {fc['temp_min']:.0f}° / {fc['temp_max']:.0f}°<br>
                💧 max {fc['hum_max']:.0f}%<br>
                ☔ {fc['precip_sum']:.1f} mm
            </p>
        """, unsafe_allow_html=True)
        
        if fc["suitable_ranges"]:
            chips = "".join([f'<span class="suitable-chip">🟢 {r}</span>' for r in fc["suitable_ranges"]])
            st.markdown(f'<div style="margin: 0.5rem 0">{chips}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="margin:0.5rem 0; color:#ff9c9c;">🔴 Không có giờ phù hợp</div>', unsafe_allow_html=True)
        
        with st.expander(f"📋 Xem chi tiết từng giờ - {fc['day_name']}"):
            df_display = fc["df_hourly"][["hour_label", "temperature", "humidity", "rain", "suitable"]].copy()
            df_display.columns = ["Giờ", "Nhiệt độ (°C)", "Độ ẩm (%)", "Mưa (mm)", "Phù hợp"]
            def highlight(row):
                return ['background-color: #2e7d32' if row["Phù hợp"] else ''] * len(row)
            st.dataframe(df_display.style.apply(highlight, axis=1), use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# ---------- Footer ----------
st.markdown(f"""
<div class="footer-note">
    <i class="fas fa-map-marker-alt"></i> {province_display}{f' - {district_display}' if district_display != "Trung tâm" else ''} &nbsp;|&nbsp;
    <i class="fas fa-globe"></i> Tọa độ: {lat:.5f}, {lon:.5f} &nbsp;|&nbsp;
    <i class="fas fa-database"></i> Dữ liệu: Open-Meteo &nbsp;|&nbsp;
    <i class="fas fa-clock"></i> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
</div>
""", unsafe_allow_html=True)
