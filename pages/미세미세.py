import streamlit as st
import pandas as pd
import urllib.request
import json
from pandas import json_normalize
from urllib.parse import urlencode, quote_plus, unquote
import plotly.express as px
import re

# --- 24:00 처리 함수 ---
def fix_24hour_times(dt_series):
    def fix_time(s):
        if isinstance(s, str) and re.match(r"\d{4}-\d{2}-\d{2} 24:00", s):
            day = pd.to_datetime(s[:10])
            day = day + pd.Timedelta(days=1)
            return day.strftime('%Y-%m-%d') + " 00:00"
        return s
    return dt_series.apply(fix_time)

# --- 데이터 요청 함수 ---
@st.cache_data(show_spinner=False)
def get_air_quality_df(station='인계동', rows=300):
    api = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty'
    key = unquote('8imLOEIhmGIxq8Ud7TglAuHG2zQ%2BA2wGRiPnVhbHb60UJDhwJlbMqzv4SOTE5B9D3Moc713ob6bioiJywC3S3Q%3D%3D')
    queryParams = '?' + urlencode({
        quote_plus('serviceKey'): key,
        quote_plus('returnType'): 'json',
        quote_plus('numOfRows'): str(rows),
        quote_plus('pageNo'): '1',
        quote_plus('stationName'): station,
        quote_plus('dataTerm'): '3MONTH',
        quote_plus('ver'): '1.0'
    })
    url = api + queryParams
    text = urllib.request.urlopen(url).read().decode('utf-8')
    json_return = json.loads(text)
    get_data = json_return.get('response')
    df = json_normalize(get_data['body']['items'])
    return df

# --- Streamlit App UI ---
st.set_page_config("인계동 미세먼지 시각화", layout="wide", page_icon="🌫️")
st.title("🌫️ 인계동 미세먼지 실시간 시각화")
st.caption("공공데이터포털 환경부 OpenAPI 활용, 최근 3개월간 데이터 (출처: 에어코리아)")

# 데이터 불러오기
with st.spinner('데이터 불러오는 중...'):
    df = get_air_quality_df('인계동', 300)

# 컬럼 한글 라벨링
col_map = {
    'dataTime': '측정시각',
    'pm10Value': '미세먼지(PM10) ㎍/㎥',
    'pm25Value': '초미세먼지(PM2.5) ㎍/㎥',
    'o3Value': '오존(O3) ppm',
    'no2Value': '이산화질소(NO2) ppm',
    'coValue': '일산화탄소(CO) ppm',
    'so2Value': '아황산가스(SO2) ppm',
    'khaiValue': '통합대기환경지수',
}

# 컬럼 정리 및 타입 변환
df = df[[*col_map.keys()]].copy()
df.rename(columns=col_map, inplace=True)

# 24:00 처리 먼저!
df['측정시각'] = fix_24hour_times(df['측정시각'])
df['측정시각'] = pd.to_datetime(df['측정시각'], format='%Y-%m-%d %H:%M')

# 숫자형 컬럼 변환
for c in col_map.values():
    if 'ppm' in c or '㎍/㎥' in c or '지수' in c:
        df[c] = pd.to_numeric(df[c], errors='coerce')

# 최신 측정값 하이라이트
latest = df.iloc[0]
st.subheader(f"가장 최근 측정 ({latest['측정시각']:%Y-%m-%d %H:%M})")
st.metric("통합대기환경지수 (KHAI)", latest['통합대기환경지수'])
cols = st.columns(4)
cols[0].metric("미세먼지 (PM10)", f"{latest['미세먼지(PM10) ㎍/㎥']} ㎍/㎥")
cols[1].metric("초미세먼지 (PM2.5)", f"{latest['초미세먼지(PM2.5) ㎍/㎥']} ㎍/㎥")
cols[2].metric("오존 (O3)", f"{latest['오존(O3) ppm']} ppm")
cols[3].metric("이산화질소 (NO2)", f"{latest['이산화질소(NO2) ppm']} ppm")

st.markdown("---")

# 꺾은선 그래프 - 미세먼지, 초미세먼지
st.subheader("최근 미세먼지/초미세먼지 변화 추이")
fig = px.line(
    df.sort_values('측정시각'), x='측정시각',
    y=['미세먼지(PM10) ㎍/㎥', '초미세먼지(PM2.5) ㎍/㎥'],
    labels={"value": "농도(㎍/㎥)", "측정시각": "시간", "variable": "항목"},
    markers=True,
    template="plotly_white"
)
fig.update_layout(legend=dict(title="항목"), height=350)
st.plotly_chart(fig, use_container_width=True)

# 오존, 이산화질소 등 추가 그래프
with st.expander("추가 대기오염물질 (오존, 이산화질소 등)"):
    fig2 = px.line(
        df.sort_values('측정시각'), x='측정시각',
        y=['오존(O3) ppm', '이산화질소(NO2) ppm', '일산화탄소(CO) ppm', '아황산가스(SO2) ppm'],
        labels={"value": "농도(ppm)", "측정시각": "시간", "variable": "항목"},
        markers=True,
        template="plotly_white"
    )
    fig2.update_layout(legend=dict(title="항목"), height=350)
    st.plotly_chart(fig2, use_container_width=True)

# 데이터 테이블 보기
with st.expander("📋 전체 데이터 테이블 (최근순)"):
    st.dataframe(df.style.highlight_max(axis=0), height=400)

# 다운로드 기능
csv = df.to_csv(index=False, encoding='utf-8-sig')
st.download_button("📥 데이터 CSV로 다운로드", csv, file_name="인계동_미세먼지.csv", mime="text/csv")