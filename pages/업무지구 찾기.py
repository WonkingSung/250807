import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 데이터 로드
DATA_PATH = '2507sub.csv'
df = pd.read_csv(DATA_PATH)

# 2. 시간대 레이블
TIME_LABELS = [f"{str(h).zfill(2)}:00~{str(h).zfill(2)}:59" for h in range(4, 24)] + \
              [f"{str(h).zfill(2)}:00~{str(h).zfill(2)}:59" for h in range(0, 4)]
승차_cols = [f"{label}_승차" for label in TIME_LABELS]
하차_cols = [f"{label}_하차" for label in TIME_LABELS]

# 3. 컬럼명 정제
df.columns = ['호선', '역'] + [item for pair in zip(승차_cols, 하차_cols) for item in pair] + ['기타']

# 4. 숫자형 컬럼 콤마(,) 제거 및 float 변환
num_cols = 승차_cols + 하차_cols
for col in num_cols:
    df[col] = df[col].astype(str).str.replace(',', '', regex=False).replace('', '0').astype(float)

# 5. 호선 선택
line = st.selectbox("호선 선택", sorted(df['호선'].unique()))
df_line = df[df['호선'] == line].copy()

# 6. 시간 인덱스 지정
morning_idx = list(range(2, 7))   # 06~10시 (index 2~6)
evening_idx = list(range(12, 17)) # 16~20시 (index 12~16)

def calc_wdi(row):
    승차 = row[승차_cols].values
    하차 = row[하차_cols].values
    total = 승차.sum() + 하차.sum() + 1e-8  # 0 나눗셈 방지

    morning_off = 하차[morning_idx].sum() / total
    evening_on = 승차[evening_idx].sum() / total
    morning_on = 승차[morning_idx].sum() / total
    evening_off = 하차[evening_idx].sum() / total

    return (morning_off + evening_on) - (morning_on + evening_off)

df_line['업무지구지수'] = df_line.apply(calc_wdi, axis=1)

# 7. 시각화
fig = px.bar(
    df_line.sort_values('업무지구지수', ascending=False),
    x='역',
    y='업무지구지수',
    color='업무지구지수',
    color_continuous_scale='blues',
    title=f"{line} 역별 업무지구 지수 (높을수록 업무지구 가능성↑)",
)
fig.update_layout(xaxis_tickangle=-45, margin=dict(b=150))

st.plotly_chart(fig, use_container_width=True)
st.dataframe(df_line[['역', '업무지구지수']].sort_values('업무지구지수', ascending=False), use_container_width=True)

