import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 페이지 설정
st.set_page_config(page_title="골프 스코어 매니저", layout="centered")
st.title("⛳ 실시간 골프 스코어 (Direct Connect)")

# --- 1. 구글 시트 연결 설정 ---
# st.connection이 Secrets에 있는 정보를 자동으로 찾아 연결합니다.
conn = st.connection("gsheets", type=GSheetsConnection)

# 시트 URL (Hildesheim CC 등 기록을 관리하는 시트 주소)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1kibXqaHam0Bt44Fi7_cRapAvfdNALjbbw-rRx6-_oBI/edit?gid=0#gid=0"

# --- 2. 데이터 불러오기 함수 ---
@st.cache_data(ttl=60)
def fetch_data():
    # 시트의 첫 번째 워크시트를 데이터프레임으로 읽어옵니다.
    return conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")

df = fetch_data()

# --- 3. UI 및 기록 추가 섹션 ---
with st.expander("📝 라운딩 기록 추가"):
    with st.form("score_form", clear_on_submit=True):
        date = st.date_input("라운딩 일자")
        course = st.text_input("골프장 이름")
        name = st.text_input("플레이어 이름")
        
        col1, col2 = st.columns(2)
        target = col1.number_input("목표 타수", 70, 120, 80)
        actual = col2.number_input("실제 타수", 60, 150, 90)
        
        c1, c2, c3 = st.columns(3)
        birdie = c1.number_input("버디", 0, 18, 0)
        par = c2.number_input("파", 0, 18, 0)
        bogey = c3.number_input("보기", 0, 18, 0)
        
        submit = st.form_submit_button("기록 저장하기")
        
        if submit:
            if not course or not name:
                st.error("모든 정보를 입력해주세요.")
            else:
                # 새 행 데이터 준비
                new_data = pd.DataFrame([{
                    "일자": str(date),
                    "골프장": course,
                    "이름": name,
                    "목표": target,
                    "실제": actual,
                    "차이": actual - target,
                    "버디": birdie,
                    "파": par,
                    "보기": bogey
                }])
                
                # 기존 데이터에 추가하여 업데이트
                updated_df = pd.concat([df, new_data], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, data=updated_df)
                
                st.success("기록이 성공적으로 저장되었습니다!")
                st.cache_data.clear() # 캐시 초기화
                st.rerun()

# --- 4. 분석 및 리더보드 섹션 ---
if not df.empty:
    st.divider()
    # 숫자 형변환
    for col in ['실제', '버디', '파', '보기']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    st.subheader("🏆 전체 현황")
    st.dataframe(df, use_container_width=True)

    m1, m2 = st.columns(2)
    m1.metric("버디 킹", df.loc[df['버디'].idxmax(), '이름'], f"{int(df['버디'].max())}개")
    m2.metric("최저 타수", df.loc[df['실제'].idxmin(), '이름'], f"{int(df['실제'].min())}타")
else:
    st.info("기록을 먼저 입력해주세요.")