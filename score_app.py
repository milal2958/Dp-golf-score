import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 구글 시트 연결 함수 ---
def get_gspread_client():
    # JSON 파일 경로 (파일이름이 google_key.json 인 경우)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google_key.json", scope)
    return gspread.authorize(creds)

# 데이터 불러오기
def fetch_data():
    try:
        client = get_gspread_client()
        # 시트 이름이나 URL로 열기
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1kibXqaHam0Bt44Fi7_cRapAvfdNALjbbw-rRx6-_oBI/edit?gid=0#gid=0").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"데이터 읽기 실패: {e}")
        return pd.DataFrame()

# 데이터 추가하기
def add_data(row_list):
    try:
        client = get_gspread_client()
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1kibXqaHam0Bt44Fi7_cRapAvfdNALjbbw-rRx6-_oBI/edit?gid=0#gid=0").sheet1
        sheet.append_row(row_list)
        return True
    except Exception as e:
        st.error(f"데이터 저장 실패: {e}")
        return False

# --- UI 부분 ---
st.set_page_config(page_title="골프 스코어 매니저", layout="centered")
st.title("⛳ 실시간 골프 스코어 (gspread)")

df = fetch_data()

with st.expander("📝 라운딩 기록 추가"):
    with st.form("score_form", clear_on_submit=True):
        date = st.date_input("라운딩 일자")
        course = st.text_input("골프장 이름")
        name = st.text_input("플레이어 이름")
        
        col1, col2 = st.columns(2)
        target = col1.number_input("목표 타수", 70, 120, 80)
        actual = col2.number_input("실제 타수", 60, 150, 90)
        
        st.write("**기록 상세**")
        c1, c2, c3 = st.columns(3)
        birdie = c1.number_input("버디", 0, 18, 0)
        par = c2.number_input("파", 0, 18, 0)
        bogey = c3.number_input("보기", 0, 18, 0)
        
        submit = st.form_submit_button("기록 저장하기")
        
        if submit:
            if not course or not name:
                st.error("모든 정보를 입력해주세요.")
            else:
                # 리스트 형태로 한 줄 데이터 준비 (시트의 컬럼 순서와 맞춰야 함)
                new_row = [
                    str(date), course, name, target, actual, 
                    actual - target, birdie, par, bogey
                ]
                
                if add_data(new_row):
                    st.success("성공적으로 저장되었습니다!")
                    st.rerun()

# --- 분석 및 리더보드 섹션 ---
if not df.empty:
    st.divider()
    # 숫자로 변환 (idxmax 오류 방지)
    for col in ['실제', '버디', '파', '보기']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    st.subheader("🏆 전체 현황")
    st.dataframe(df, use_container_width=True)

    # 간단 메트릭
    m1, m2 = st.columns(2)
    m1.metric("버디 킹", df.loc[df['버디'].idxmax(), '이름'], f"{int(df['버디'].max())}개")
    m2.metric("최저 타수", df.loc[df['실제'].idxmin(), '이름'], f"{int(df['실제'].min())}타")
else:
    st.info("기록을 먼저 입력해주세요.")