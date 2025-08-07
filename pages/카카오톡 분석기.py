import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import re
import emoji
from urlextract import URLExtract

st.title("카카오톡 채팅 데이터 분석 & 시각화")

uploaded_file = st.file_uploader("카카오톡 채팅 CSV 파일을 업로드하세요", type="csv")

if uploaded_file:
    # 1. 데이터 불러오기 및 전처리
    df = pd.read_csv(uploaded_file)
    df.columns = ['date_time', 'user_name', 'text']
    df.dropna(subset=['date_time', 'user_name', 'text'], inplace=True)
    df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')

    # 날짜 파생 변수
    df['year'] = df['date_time'].dt.year
    df['month'] = df['date_time'].dt.month
    df['day'] = df['date_time'].dt.day
    df['weekday'] = df['date_time'].dt.day_name()
    df['hour'] = df['date_time'].dt.hour

    # 메시지 길이/단어수
    df['msg_len'] = df['text'].str.len()
    df['msg_word_count'] = df['text'].str.split().str.len()

    # 사진/동영상 탐지
    av_pattern = '^동영상$|^사진$|^사진 [0-9]{1,2}장$'
    df['audio_visual'] = df['text'].str.contains(av_pattern, na=False).astype(int)

    # 이모지/비언어적 표현
    def extract_emojis(text):
        return [e['emoji'] for e in emoji.emoji_list(str(text))]
    mimetic = "[ㅋㅎㅠㅜ!?~]+"
    punctuations = "[,.]{2,}"
    emo_type1 = "[;:]{1}[\^\'-]?[)(DPpboOX]"
    emo_type2 = "[>ㅜㅠㅡ@\^][ㅁㅇ0oO\._\-]*[\^ㅜㅠㅡ@<];*"
    emo_type3 = r"\(.+?\)"
    nonverbal_list = [mimetic, punctuations, emo_type1, emo_type2, emo_type3]
    df['nonverbal'] = df['text'].str.findall('|'.join(nonverbal_list)) + df['text'].map(extract_emojis)
    df['nonverbal_count'] = df['nonverbal'].apply(len)

    # URL 추출
    extractor = URLExtract()
    df['url'] = df['text'].apply(lambda x: extractor.find_urls(str(x)))
    df['url_count'] = df['url'].apply(len)

    # 단어 추출 (한글/영문 2글자 이상만, 일부 불용어 제거)
    stopwords = set(['이모티콘','사진','동영상','것','거','수','좀','더','이','저','그','그리고','등','ㅋㅋ','ㅎㅎ'])
    def extract_words(text):
        words = re.findall(r'[가-힣a-zA-Z]{2,}', str(text))
        return [w.lower() for w in words if w not in stopwords]
    df['tokens'] = df['text'].apply(extract_words)

    tabs = st.tabs(['기본 통계', '메시지/사용자 분석', '비언어적 표현', '단어 빈도 & 매트릭스', '개별 사용자 단어'])

    # 1. 기본 통계
    with tabs[0]:
        st.header('기본 통계/정보')
        st.write(df.head())
        st.metric("총 메시지 수", len(df))
        st.metric("참여 사용자 수", df['user_name'].nunique())
        st.write("날짜 범위:", df['date_time'].min(), " ~ ", df['date_time'].max())

        st.plotly_chart(px.histogram(df, x='date_time', nbins=100, title="메시지 일별 분포"), use_container_width=True)
        st.plotly_chart(px.histogram(df, x='hour', title="메시지 시간대 분포"), use_container_width=True)
        st.plotly_chart(px.histogram(df, x='user_name', title="사용자별 메시지 수"), use_container_width=True)

    # 2. 메시지/사용자 분석
    with tabs[1]:
        st.header("메시지 길이/단어수/산점도")
        st.plotly_chart(px.histogram(df, x='msg_len', title="메시지 길이 분포"), use_container_width=True)
        st.plotly_chart(px.histogram(df, x='msg_word_count', title="메시지 단어수 분포"), use_container_width=True)
        st.plotly_chart(px.scatter(df, x='msg_len', y='msg_word_count', title="메시지 길이 vs 단어수 산점도", hover_name='user_name', hover_data=['text']), use_container_width=True)

        st.header("상위 15명 사용자별 메시지 길이 박스플롯")
        top_users = df['user_name'].value_counts().nlargest(15).index
        subset_df = df[df['user_name'].isin(top_users) & (df['msg_len'] < 100)]
        st.plotly_chart(px.box(subset_df, x='user_name', y='msg_len', title='상위 15명 메시지 길이 분포'), use_container_width=True)

    # 3. 비언어적 표현 분석
    with tabs[2]:
        st.header("비언어적 표현 (이모지/의성어/이모티콘 등)")
        st.plotly_chart(px.histogram(df, x='nonverbal_count', title="비언어적 표현 포함 메시지 개수"), use_container_width=True)
        st.write("비언어적 표현 예시:", df.loc[df['nonverbal_count'] > 0, ['user_name','text','nonverbal']].head(10))

        st.header("사용자별 비언어 표현 매트릭스")
        # ---- (여기서 중복라벨 문제 완벽 해결) ----
        nonverbal_df = df[df['nonverbal_count'] > 0].explode('nonverbal')
        top15_users = nonverbal_df['user_name'].value_counts().nlargest(15).index
        top_nonverbals = nonverbal_df['nonverbal'].value_counts().nlargest(20).index
        filtered_nv = nonverbal_df[
            (nonverbal_df['user_name'].isin(top15_users)) &
            (nonverbal_df['nonverbal'].isin(top_nonverbals))
        ]
        pivot = pd.crosstab(
            filtered_nv['user_name'],
            filtered_nv['nonverbal'],
            normalize='index'
        )
        st.plotly_chart(
            px.imshow(
                pivot,
                aspect='auto',
                color_continuous_scale='Viridis',
                title="상위 15명 사용자 - 비언어 표현 매트릭스",
                height=40*len(pivot)+200
            ),
            use_container_width=True
        )

    # 4. 단어 빈도/매트릭스
    with tabs[3]:
        st.header("단어 빈도/매트릭스/차트")
        all_tokens = sum(df['tokens'], [])
        word_counts = Counter(all_tokens)
        top_words_df = pd.DataFrame(word_counts.most_common(50), columns=['word','count'])

        # Bar
        st.plotly_chart(px.bar(top_words_df.head(20).sort_values('count'), x='count', y='word', orientation='h', title='상위 20개 단어 (Bar Chart)'), use_container_width=True)
        # Pie
        st.plotly_chart(px.pie(top_words_df.head(10), names='word', values='count', title='상위 10개 단어 (Pie Chart)'), use_container_width=True)
        # Treemap
        st.plotly_chart(px.treemap(top_words_df, path=[px.Constant("단어"), 'word'], values='count', title='상위 50개 단어 Treemap'), use_container_width=True)
        # Bubble
        st.plotly_chart(px.scatter(top_words_df.head(30), x='word', y='count', size='count', title='상위 30개 단어 버블 차트'), use_container_width=True)

        st.header("상위 20명-20단어 빈도 매트릭스")
        top20_users = df['user_name'].value_counts().nlargest(20).index
        top20_words = top_words_df.head(20)['word'].tolist()
        filtered_df = df[df['user_name'].isin(top20_users)]
        # explode 후에도 반드시 필터 적용!
        filtered_long = filtered_df.explode('tokens')
        filtered_long = filtered_long[filtered_long['tokens'].isin(top20_words)]
        # 피벗 생성
        long_df = pd.crosstab(
            filtered_long['user_name'],
            filtered_long['tokens'],
            normalize=False
        ).reindex(index=top20_users, columns=top20_words, fill_value=0)
        st.plotly_chart(px.imshow(long_df, labels=dict(x="단어", y="사용자", color="빈도"), color_continuous_scale="Blues", aspect="auto", height=40*len(long_df)+200, title="상위 20명-20단어 사용 빈도 매트릭스"), use_container_width=True)

    # 5. 개별 사용자별 많이 쓴 단어 Top 20
    with tabs[4]:
        st.header("개별 사용자별 많이 쓴 단어 Top 20 (Bar Chart)")
        user_sel = st.selectbox("사용자를 선택하세요", df['user_name'].unique())
        user_tokens = df.loc[df['user_name'] == user_sel, 'tokens'].explode()
        word_count = Counter(user_tokens)
        user_top20 = pd.DataFrame(word_count.most_common(20), columns=['word','count'])
        st.plotly_chart(px.bar(user_top20.sort_values('count'), x='count', y='word', orientation='h', title=f'[{user_sel}] 많이 사용한 단어 Top 20'), use_container_width=True)

    st.success("분석이 완료되었습니다. 다양한 시각화를 확인하세요!")

else:
    st.info("먼저 카카오톡 csv 파일을 업로드하세요.")
