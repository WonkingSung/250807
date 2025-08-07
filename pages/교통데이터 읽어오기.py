import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# 데이터 파일 경로
DATA_PATH = '2507sub.csv'

# 시간대 레이블 생성 (예: 04:00~04:59 ~ 03:00~03:59)
TIME_LABELS = [f"{str(h).zfill(2)}:00~{str(h).zfill(2)}:59" for h in range(4, 24)] + \
              [f"{str(h).zfill(2)}:00~{str(h).zfill(2)}:59" for h in range(0, 4)]

# 1. 데이터 로드
df = pd.read_csv(DATA_PATH)

# 2. 컬럼명 맞추기
df.columns = ['호선', '역'] + [f"{label}_{tp}" for label in TIME_LABELS for tp in ['승차', '하차']] + ['기타']

# 3. 호선/역 선택
line = st.selectbox("호선 선택", sorted(df['호선'].unique()))
filtered = df[df['호선'] == line]
station = st.selectbox("역 선택", sorted(filtered['역'].unique()))

row = filtered[filtered['역'] == station].iloc[0]

승차값 = [row[f"{t}_승차"] for t in TIME_LABELS]
하차값 = [row[f"{t}_하차"] for t in TIME_LABELS]

# 4. Plotly 그래프
fig = go.Figure()
fig.add_trace(go.Scatter(x=TIME_LABELS, y=승차값, mode='lines+markers', name='승차'))
fig.add_trace(go.Scatter(x=TIME_LABELS, y=하차값, mode='lines+markers', name='하차'))
fig.update_layout(
    title=f"{line} {station} 시간대별 승차/하차 인원",
    xaxis_title="시간대",
    yaxis_title="이용객 수",
    xaxis=dict(tickangle=-45),
    legend=dict(x=0.01, y=0.99),
    margin=dict(l=30, r=30, t=60, b=150)
)
st.plotly_chart(fig, use_container_width=True)

