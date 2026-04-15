import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="골프 스코어 매니저", layout="centered")
st.title("⛳ 실시간 골프 스코어 (Google Sheets)")

# 1. 시트 설정
# 주의: 'edit#gid=0' 부분을 지우고 메인 주소만 입력하는 것이 더 안정적입니다.
spreadsheet = "https://docs.google.com/spreadsheets/d/1kibXqaHam0Bt44Fi7_cRapAvfdNALjbbw-rRx6-_oBI/"

conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 불러오기
def fetch_data():
    # ttl=0은 캐시를 사용하지 않고 항상 최신 데이터를 가져오게 합니다.
    return conn.read(spreadsheet=spreadsheet, ttl=0)

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
                new_entry = pd.DataFrame([{
                    '일자': str(date),
                    '골프장': course,
                    '이름': name,
                    '목표': int(target),
                    '실제': int(actual),
                    '차이': int(actual - target),
                    '버디': int(birdie),
                    '파': int(par),
                    '보기': int(bogey)
                }])
                
                # 데이터 병합
                updated_df = pd.concat([df, new_entry], ignore_index=True)
                
                # [수정포인트] 시트 이름(worksheet)을 명시적으로 "Sheet1"으로 지정
                # 구글 시트 하단 탭 이름이 '시트1' 이라면 "시트1"로 적어야 합니다.
                try:
                    conn.update(spreadsheet=spreadsheet, worksheet="Sheet1", data=updated_df)
                    st.success("저장 완료!")
                    st.rerun()
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다. 구글 시트의 공유 설정(편집자 권한)을 확인해주세요.")
                    st.info("시트 하단 탭 이름이 'Sheet1'이 맞는지도 확인이 필요합니다.")

# --- 2. 분석 및 리더보드 섹션 ---
if not df.empty:
    st.divider()
    option = st.selectbox("📊 정렬 기준", ["최근순", "실제 타수 낮은순", "버디 많은순"])
    
    if option == "최근순":
        df_display = df.sort_values(by="일자", ascending=False)
    elif option == "실제 타수 낮은순":
        df_display = df.sort_values(by="실제", ascending=True)
    else:
        df_display = df.sort_values(by="버디", ascending=False)

    st.subheader("🏆 전체 랭킹")
    st.dataframe(df_display, use_container_width=True)

    # 부문별 1위 (데이터 확인 후 표시)
    st.subheader("🎖️ 오늘의 부문별 베스트")
    m1, m2, m3 = st.columns(3)
    
    try:
        m1.metric("버디 킹", df.loc[df['버디'].idxmax(), '이름'], f"{int(df['버디'].max())}개")
        m2.metric("파 콜렉터", df.loc[df['파'].idxmax(), '이름'], f"{int(df['파'].max())}개")
        m3.metric("보기 대장", df.loc[df['보기'].idxmax(), '이름'], f"{int(df['보기'].max())}개")
    except:
        st.write("데이터가 더 필요합니다.")
else:
