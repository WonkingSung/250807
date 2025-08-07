import streamlit as st
import pandas as pd
import plotly.express as px

st.title("CSV 업로드 & 시각화")

# 1. CSV 업로드
file = st.file_uploader("CSV 파일 업로드", type="csv")

if file:
    # 2. CSV 읽고 표로 보여주기
    df = pd.read_csv(file)
    st.dataframe(df)

    # 3. 숫자형 컬럼만 가져오기
    num_cols = df.select_dtypes('number').columns

    # 4. X, Y축 선택 후 Plotly 그래프 그리기
    if len(num_cols) >= 2:
        x = st.selectbox("X축 선택", num_cols)
        y = st.selectbox("Y축 선택", num_cols, index=1)
        st.plotly_chart(px.scatter(df, x=x, y=y, title=f"{x} vs {y}"), use_container_width=True)
    else:
        st.warning("숫자형 컬럼이 2개 이상 있어야 그래프를 그릴 수 있어요!")
else:
    st.info("CSV 파일을 업로드해 주세요.")
