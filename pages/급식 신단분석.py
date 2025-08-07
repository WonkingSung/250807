import streamlit as st
import requests
import datetime
import re

st.set_page_config(page_title="오늘의 삼일고 급식", page_icon="🍱", layout="centered")

st.title("🍱 삼일고 급식 정보")
st.caption("원하는 날짜를 선택해 급식 정보를 확인하세요.")

# 1. 달력 위젯으로 날짜 선택 (기본값: 오늘)
selected_date = st.date_input(
    "날짜를 선택하세요",
    value=datetime.date.today(),
    min_value=datetime.date(2020, 1, 1),  # 데이터가 있는 최소 날짜로 지정(조정 가능)
    max_value=datetime.date.today() + datetime.timedelta(days=60)  # 미래 2달까지
)
date_str = selected_date.strftime("%Y%m%d")  # yyyymmdd

# 2. NEIS 오픈 API 파라미터
api_url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
params = {
    "ATPT_OFCDC_SC_CODE": "J10",         # 경기도교육청
    "SD_SCHUL_CODE": "7531427",          # 삼일고등학교 코드
    "Type": "json",
    "MLSV_YMD": date_str
}

# 3. API 요청 및 예외처리
try:
    response = requests.get(api_url, params=params, timeout=5)
    data = response.json()

    if "mealServiceDietInfo" in data:
        rows = data['mealServiceDietInfo'][1]['row']
        st.subheader(f"📅 {selected_date.strftime('%Y년 %m월 %d일')} 급식 메뉴")

        for row in rows:
            meal_name = row.get('MMEAL_SC_NM', '급식')
            dish_str = row.get('DDISH_NM', '')

            # 클리닝
            cleaned = dish_str.replace('<br/>', '\n')
            cleaned = re.sub(r'\d', '', cleaned)         # 숫자 제거
            cleaned = re.sub(r'[().]', '', cleaned)      # 괄호/점 제거
            cleaned = re.sub(r' +', ' ', cleaned)        # 다중 공백 정리

            # 카드 스타일 출력
            with st.container():
                st.markdown(
                    f"""
                    <div style='
                        background-color:#F5F5F5;
                        border-radius:18px;
                        box-shadow:0 4px 12px #0001;
                        padding: 20px 24px;
                        margin-bottom: 18px;'>
                        <h4 style='color:#2A5D9F; margin-bottom:8px'>{meal_name}</h4>
                        <pre style='font-size:1.1em; color:#222'>{cleaned.strip()}</pre>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    else:
        st.error("해당 날짜에 급식 정보가 없습니다. (공휴일/방학/에러 등)")
        st.image("https://cdn.pixabay.com/photo/2017/01/31/19/13/food-2023955_1280.png", width=220)

except Exception as e:
    st.error("급식 정보 불러오기 실패! 다시 시도해보세요.")
    st.write(f"에러 상세: {e}")