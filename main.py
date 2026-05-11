import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import List

# ---------- Cấu hình trang ----------
st.set_page_config(
    page_title="Gunpla Spray Day",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- JavaScript tự động lấy vị trí khi chưa có tọa độ ----------
st.markdown("""
<script>
    // Kiểm tra nếu URL chưa có tham số lat, lon
    const urlParams = new URLSearchParams(window.location.search);
    if (!urlParams.has('lat') || !urlParams.has('lon')) {
        // Yêu cầu vị trí
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    // Chuyển hướng đến cùng URL nhưng thêm lat, lon
                    const newUrl = new URL(window.location.href);
                    newUrl.searchParams.set('lat', lat);
                    newUrl.searchParams.set('lon', lon);
                    window.location.href = newUrl.toString();
                },
                (error) => {
                    // Lỗi: dùng tọa độ mặc định (Cần Thơ)
                    console.error('Lỗi lấy vị trí:', error);
                    const defaultLat = 10.072732;
                    const defaultLon = 105.806206;
                    const newUrl = new URL(window.location.href);
                    newUrl.searchParams.set('lat', defaultLat);
                    newUrl.searchParams.set('lon', defaultLon);
                    window.location.href = newUrl.toString();
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
        } else {
            // Trình duyệt không hỗ trợ, dùng mặc định
            const defaultLat = 10.072732;
            const defaultLon = 105.806206;
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.set('lat', defaultLat);
            newUrl.searchParams.set('lon', defaultLon);
            window.location.href = newUrl.toString();
        }
    }
</script>
""", unsafe_allow_html=True)

# ---------- Đọc tọa độ từ query params ----------
params = st.query_params
if "lat" in params and "lon" in params:
    try:
        lat = float(params["lat"][0]) if isinstance(params["lat"], list) else float(params["lat"])
        lon = float(params["lon"][0]) if isinstance(params["lon"], list) else float(params["lon"])
        # Kiểm tra hợp lệ
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            lat, lon = 10.072732, 105.806206
    except Exception:
        lat, lon = 10.072732, 105.806206
else:
    # Trường hợp không có tham số (có thể do script chưa kịp chạy)
    # Nhưng script sẽ redirect, nên đây là fallback an toàn
    lat, lon = 10.072732, 105.806206

# ---------- Custom CSS (giữ nguyên phần đẹp) ----------
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
    .condition-badge { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 40px; font-size: 0.85rem; font-weight: 600; }
    .badge-good { background: #1a3a32; color: #8effd2; border: 1px solid #2e9b7c; }
    .badge-bad { background: #441f2c; color: #ff9c9c; border: 1px solid #c54f5f; }
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

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🎨 Gunpla Spray")
    st.markdown("---")
    
    # Hiển thị tọa độ hiện tại (có thể chỉnh sửa thủ công)
    lat = st.number_input("Vĩ độ", value=lat, format="%.6f", key="lat_input")
    lon = st.number_input("Kinh độ", value=lon, format="%.6f", key="lon_input")
    st.caption("📍 Tọa độ hiện tại (có thể thay đổi)")
    
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

# ---------- Helper functions ----------
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

# Fetch data
try:
    data = fetch_weather_data(lat, lon)
except Exception as e:
    st.error(f"❌ Không thể lấy dữ liệu thời tiết: {e}")
    st.stop()

current = data["current"]
hourly = data["hourly"]
daily = data["daily"]

# Thời tiết hiện tại
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

# Giờ phù hợp hôm nay
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

# Dự báo 3 ngày
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

# Footer
st.markdown(f"""
<div class="footer-note">
    <i class="fas fa-map-marker-alt"></i> Tọa độ: {lat:.6f}, {lon:.6f} &nbsp;|&nbsp;
    <i class="fas fa-database"></i> Dữ liệu: Open-Meteo &nbsp;|&nbsp;
    <i class="fas fa-clock"></i> {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}
</div>
""", unsafe_allow_html=True)
