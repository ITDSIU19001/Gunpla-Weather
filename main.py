import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# ---------- Cấu hình trang ----------
st.set_page_config(
    page_title="Gunpla Spray Day",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Hàm helper ----------
@st.cache_data(ttl=1800)  # cache 30 phút
def fetch_weather_data(lat: float, lon: float):
    """Gọi API Open-Meteo, trả về dict current, hourly, daily."""
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
    """Nhóm các giờ liên tiếp (định dạng 'HH:MM') thành khoảng."""
    if not hour_strings:
        return []
    # Chuyển sang số giờ
    hours = [int(h.split(':')[0]) for h in hour_strings]
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
    # xử lý đoạn cuối
    if start == prev:
        ranges.append(f"{start:02d}:00")
    else:
        ranges.append(f"{start:02d}:00-{prev:02d}:00")
    return ranges

def is_suitable(temp: float, humidity: float, rain: float,
                temp_min: float, temp_max: float, hum_max: float, rain_max: float) -> bool:
    """Kiểm tra điều kiện phù hợp với ngưỡng do người dùng thiết lập."""
    return (temp_min <= temp <= temp_max) and (humidity <= hum_max) and (rain < rain_max)

def process_hourly_data(hourly: Dict, target_date: str, conditions: Dict) -> pd.DataFrame:
    """Trích xuất dữ liệu theo giờ cho một ngày, thêm cột phù hợp."""
    times = hourly["time"]
    temps = hourly["temperature_2m"]
    hums = hourly["relative_humidity_2m"]
    rains = hourly["precipitation"]

    rows = []
    for t, tmp, hum, rn in zip(times, temps, hums, rains):
        if t.startswith(target_date):
            suitable = is_suitable(tmp, hum, rn,
                                    conditions["temp_min"], conditions["temp_max"],
                                    conditions["hum_max"], conditions["rain_max"])
            rows.append({
                "time": t,
                "hour_label": t.split("T")[1][:5],
                "temperature": tmp,
                "humidity": hum,
                "rain": rn,
                "suitable": suitable
            })
    return pd.DataFrame(rows)

def get_suitable_ranges(df: pd.DataFrame) -> List[str]:
    """Từ DataFrame hourly, lấy danh sách giờ phù hợp và nhóm thành khoảng."""
    suitable_hours = df[df["suitable"]]["hour_label"].tolist()
    return group_consecutive_hours(suitable_hours)

# ---------- Giao diện chính ----------
st.markdown("""
    <h1 style='text-align: center;'>
        <i class='fas fa-spray-can-sparkles'></i> Gunpla Spray Day
    </h1>
    <p style='text-align: center; font-size: 1.1rem;'>Kiểm tra thời tiết, giờ phù hợp và dự báo 3 ngày 🎨</p>
""", unsafe_allow_html=True)

# Sidebar nhập thông số
st.sidebar.header("📍 Vị trí")
lat = st.sidebar.number_input("Vĩ độ", value=10.072732, format="%.6f")
lon = st.sidebar.number_input("Kinh độ", value=105.806206, format="%.6f")
st.sidebar.caption("Mặc định: Cần Thơ (10.072732, 105.806206)")

st.sidebar.header("⚙️ Điều kiện sơn")
col1, col2 = st.sidebar.columns(2)
with col1:
    temp_min = st.number_input("Nhiệt độ tối thiểu (°C)", value=18.0, step=0.5)
    hum_max = st.number_input("Độ ẩm tối đa (%)", value=65, step=1)
with col2:
    temp_max = st.number_input("Nhiệt độ tối đa (°C)", value=30.0, step=0.5)
    rain_max = st.number_input("Mưa tối đa (mm/giờ)", value=0.2, step=0.1)

conditions = {
    "temp_min": temp_min,
    "temp_max": temp_max,
    "hum_max": hum_max,
    "rain_max": rain_max
}

# Nút làm mới
if st.sidebar.button("🔄 Cập nhật thời tiết", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Fetch dữ liệu
try:
    data = fetch_weather_data(lat, lon)
except Exception as e:
    st.error(f"❌ Không thể lấy dữ liệu thời tiết: {e}")
    st.stop()

current = data["current"]
hourly = data["hourly"]
daily = data["daily"]

# ---------- Hiển thị thời tiết hiện tại ----------
st.subheader("🌡️ Thời tiết hiện tại")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Nhiệt độ", f"{current['temperature_2m']} °C")
with col2:
    st.metric("Độ ẩm", f"{current['relative_humidity_2m']} %")
with col3:
    st.metric("Lượng mưa (hiện tại)", f"{current['precipitation'] or 0:.1f} mm")
with col4:
    st.metric("Tốc độ gió", f"{current['wind_speed_10m']} m/s")

# Kiểm tra điều kiện hiện tại
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
    # Biểu đồ xu hướng nhiệt độ & độ ẩm
    st.markdown("#### 📈 Xu hướng trong ngày")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_today["hour_label"], y=df_today["temperature"],
                             mode='lines+markers', name='Nhiệt độ (°C)',
                             line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df_today["hour_label"], y=df_today["humidity"],
                             mode='lines+markers', name='Độ ẩm (%)',
                             line=dict(color='skyblue'), yaxis='y2'))
    # Vùng phù hợp tô màu
    suitable_hours = df_today[df_today["suitable"]]["hour_label"].tolist()
    if suitable_hours:
        for sh in suitable_hours:
            fig.add_vrect(x0=sh, x1=sh, line_width=0, fillcolor="green", opacity=0.2,
                          annotation_text="✓", annotation_position="top left")
    fig.update_layout(
        title="Diễn biến nhiệt độ và độ ẩm hôm nay",
        xaxis_title="Giờ",
        yaxis_title="Nhiệt độ (°C)",
        yaxis2=dict(title="Độ ẩm (%)", overlaying='y', side='right'),
        legend=dict(x=0.01, y=0.99),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Không có giờ nào phù hợp để sơn trong hôm nay.")

# ---------- Dự báo 3 ngày tới ----------
st.subheader("🗓️ Dự báo 3 ngày tới (chạm vào nút để xem chi tiết từng giờ)")
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

# Hiển thị dạng card 3 cột
cols = st.columns(3)
for idx, fc in enumerate(forecast_data):
    with cols[idx % 3]:
        # Icon thời tiết dựa trên weathercode
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
        <div style="background:#0e1117; border-radius: 20px; padding: 1rem; 
                    border: 1px solid #2c3e50; margin-bottom: 1rem;">
            <h3 style="text-align:center">{fc['day_name']} {icon}</h3>
            <p style="text-align:center">
                🌡️ {fc['temp_min']:.0f}° / {fc['temp_max']:.0f}°<br>
                💧 Độ ẩm max {fc['hum_max']:.0f}%<br>
                ☔ Tổng mưa {fc['precip_sum']:.1f} mm
            </p>
        """, unsafe_allow_html=True)
        if fc["suitable_ranges"]:
            st.markdown("**🟢 Giờ phù hợp:** " + ", ".join(fc["suitable_ranges"]))
        else:
            st.markdown("**🔴 Không có giờ phù hợp**")
        # Nút xem chi tiết từng giờ (dùng expander)
        with st.expander(f"📋 Xem chi tiết từng giờ - {fc['day_name']}"):
            df_display = fc["df_hourly"][["hour_label", "temperature", "humidity", "rain", "suitable"]].copy()
            df_display.columns = ["Giờ", "Nhiệt độ (°C)", "Độ ẩm (%)", "Mưa (mm)", "Phù hợp"]
            # Highlight dòng phù hợp
            def highlight(row):
                return ['background-color: #2e7d32' if row["Phù hợp"] else ''] * len(row)
            st.dataframe(df_display.style.apply(highlight, axis=1), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Thông tin phụ
st.caption(f"📍 Tọa độ hiện tại: {lat}, {lon} | Dữ liệu từ Open-Meteo | Cập nhật: {datetime.now().strftime('%H:%M:%S')}")
