# strealit main화면

import streamlit as st
import pandas as pd

st.title("원킹의 streamlit 연습장 😍")
st.write("스트림릿을 배우기 위해 이것저저것 시도해보고 있습니다.")
st.success("왼쪽 페이지 리스트에 다양한 프로젝트들이 있습니다. ")

# 예시 이미지 출력
st.image("https://www.dataquest.io/wp-content/uploads/2024/02/Why-Should-You-Learn-Streamlit-in-2024.png.webp")

st.divider()  # 화면 구분선
st.title("2행 2열 버튼 예제")

내용 = " "

col1, col2 = st.columns(2)
if col1.button("사랑"): 내용 ="❤️"
if col2.button("겸손 "): 내용 = "🌱"

col3, col4 = st.columns(2)
if col3.button("실존 "): 내용 = "💡"
if col4.button("협력 "):내용 = "🤝"

st.markdown(f"# {내용}")

# 연습 3 : 이미지 2행 출력
이미지열1, 이미지열2 = st.columns(2)
with 이미지열1 :
    st.image("https://i.namu.wiki/i/vPTM0_1lIRJbMIuQYDxFBs_rAKwZUi0z97j_sInLUiS99KJpWcopsb_k_2YpEvWKCNPc0-0O1cql3ci5x0JZFg.webp", width = 50)
    st.caption("상암고 이미지 ")
with 이미지열2 :
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/f3/Sangam_High_School.jpg", width = 500)
    st.caption("상암고 전경 ")