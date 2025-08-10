import streamlit as st
import requests, datetime, re, calendar
import pandas as pd
import plotly.graph_objects as go

# ────────────────────────── 0. 기본 설정 ──────────────────────────
st.set_page_config(page_title="삼일고 급식 & 영양정보",
                   page_icon="🍱", layout="centered")
st.title("🍱 삼일고 급식 & 영양정보")
st.caption("날짜를 선택해 당일 급식·영양성분을 확인하고, "
           "해당 달의 3대 영양소 추이를 CSV·그래프로 받아보세요!")

# ────────────────────────── 1. 날짜 선택 ──────────────────────────
selected_date = st.date_input(
    "날짜를 선택하세요",
    value=datetime.date.today(),
    min_value=datetime.date(2020, 1, 1),
    max_value=datetime.date.today() + datetime.timedelta(days=60)
)
weekday_kor = ['월', '화', '수', '목', '금', '토', '일']
yoil = weekday_kor[selected_date.weekday()]
date_display = selected_date.strftime(f"%Y년 %m월 %d일({yoil})")
date_str = selected_date.strftime("%Y%m%d")       # API용

# ────────────────────────── 2. NEIS API 함수 ──────────────────────────
API_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"
BASE_PARAMS = {
    "ATPT_OFCDC_SC_CODE": "J10",   # 경기도교육청
    "SD_SCHUL_CODE": "7531427",    # 삼일고
    "Type": "json",
}

@st.cache_data(show_spinner=False)
def fetch_day_rows(yyyymmdd: str):
    params = {**BASE_PARAMS, "MLSV_YMD": yyyymmdd}
    try:
        js = requests.get(API_URL, params=params, timeout=4).json()
        return js["mealServiceDietInfo"][1]["row"] if "mealServiceDietInfo" in js else None
    except Exception:
        return None

# ────────────────────────── 3. 당일 급식/영양 표시 ──────────────────────────
rows = fetch_day_rows(date_str)
if rows:
    st.subheader(f"📅 {date_display} 급식 메뉴")
    for row in rows:
        # 메뉴 전처리
        dish = (row["DDISH_NM"].replace("<br/>", "\n").replace("/n", "\n"))
        dish = re.sub(r"\d", "", dish)
        dish = re.sub(r"[().]", "", dish)
        menu_items = [m.strip() for m in dish.split("\n") if m.strip()]

        meal_name = row["MMEAL_SC_NM"]
        menu_html = "<br/>".join([f"• {i}" for i in menu_items])

        st.markdown(
            f"""
            <div style="background:#F5F5F5;border-radius:18px;
                        box-shadow:0 4px 12px #0001;padding:20px 24px;margin-bottom:12px">
                <h4 style="color:#2A5D9F;margin:0 0 8px 0">{meal_name}</h4>
                <div style="font-size:1.05em;line-height:1.6;color:#222">
                    {menu_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 당일 3대 영양소 막대그래프
        if row.get("NTR_INFO"):
            labs, vals = [], []
            for seg in row["NTR_INFO"].split("<br/>"):
                if not seg.strip(): continue
                p = re.split(r"[:：]", seg)
                if len(p) != 2: continue
                val = re.findall(r"[\d.]+", p[1])
                if val:
                    labs.append(re.sub(r"\(.*\)", "", p[0]).strip())
                    vals.append(float(val[0]))
            plot = {k: v for k, v in zip(labs, vals)
                    if k in ["탄수화물", "단백질", "지방"]}
            fig = go.Figure(go.Bar(
                x=list(plot.keys()), y=list(plot.values()),
                text=[f"{v:.1f}" for v in plot.values()],
                textposition="outside"))
            fig.update_layout(height=300, template="simple_white",
                              margin=dict(l=20, r=20, t=30, b=20),
                              yaxis_title="함량(g·mg 등)")
            st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("해당 날짜에는 급식 정보가 없습니다. (방학·공휴일 등)")

# ────────────────────────── 4. 월간 영양정보 수집 ──────────────────────────
@st.cache_data(show_spinner=True)
def get_month_df(year:int, month:int) -> pd.DataFrame:
    rec = []
    last = calendar.monthrange(year, month)[1]
    for day in range(1, last + 1):
        ymd = f"{year}{month:02d}{day:02d}"
        rows = fetch_day_rows(ymd)
        if not rows: continue
        for r in rows:
            ntr = r.get("NTR_INFO")
            if not ntr: continue
            for seg in ntr.split("<br/>"):
                if not seg.strip(): continue
                p = re.split(r"[:：]", seg)
                if len(p) != 2: continue
                label = re.sub(r"\(.*\)", "", p[0]).strip()
                v = re.findall(r"[\d.]+", p[1])
                if v and label in ["탄수화물", "단백질", "지방"]:
                    rec.append({"날짜": f"{year}-{month:02d}-{day:02d}",
                                "영양소": label,
                                "함량": float(v[0])})
    return pd.DataFrame(rec)

# ────────────────────────── 5. 월간 CSV & 그래프 ──────────────────────────
st.markdown("---")
st.markdown("### 📈 선택 달 3대 영양소 추이 & CSV")

year, month = selected_date.year, selected_date.month
df_month = get_month_df(year, month)

col1, col2 = st.columns(2)

# ── 5-1 CSV 다운로드 ──
with col1:
    if df_month.empty:
        st.info("선택 달에 영양 정보가 없습니다.")
    else:
        csv = df_month.to_csv(index=False).encode("utf-8-sig")
        fname = f"삼일고_3대영양소_{year}_{month:02d}.csv"
        st.download_button("💾 CSV 다운로드", csv, fname, mime="text/csv")

# ── 5-2 3대 영양소 꺾은선 그래프 ──
with col2:
    if not df_month.empty:
        df_pivot = (df_month
                    .groupby(["날짜", "영양소"], as_index=False)["함량"].sum()
                    .pivot(index="날짜", columns="영양소", values="함량")
                    .fillna(0))

        fig_line = go.Figure()
        for nutrient in ["탄수화물", "단백질", "지방"]:
            if nutrient in df_pivot.columns:
                fig_line.add_trace(go.Scatter(
                    x=df_pivot.index,
                    y=df_pivot[nutrient],
                    mode="lines+markers",
                    name=nutrient,
                    hovertemplate=f"{nutrient}: %{{y:.1f}}<extra></extra>"
                ))

        # 선택 날짜 세로 점선
        sel_str = selected_date.strftime("%Y-%m-%d")
        if sel_str in df_pivot.index:
            fig_line.add_shape(
                type="line", x0=sel_str, x1=sel_str, y0=0, y1=1,
                xref="x", yref="paper",
                line=dict(color="black", dash="dot", width=1.5)
            )

        fig_line.update_layout(
            height=380, template="simple_white",
            margin=dict(l=30, r=30, t=40, b=40),
            xaxis_title=f"{year}-{month:02d} 일자",
            yaxis_title="함량 (g·mg 등)",
            title="3대 영양소 일자별 섭취량",
            legend_title="영양소"
        )
        st.plotly_chart(fig_line, use_container_width=True)
