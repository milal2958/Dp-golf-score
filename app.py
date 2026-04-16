import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 모바일 최적화
st.set_page_config(page_title="골프 동호회 스코어보드", layout="wide")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 사이드바 메뉴 구성
menu = st.sidebar.selectbox("메뉴 선택", ["📝 스코어 입력", "🏆 실시간 리더보드", "🎁 오늘의 시상식", "📂 누적 데이터"])

# 24명 명단 (실제 성함으로 수정하여 사용하세요)
player_list = ["공장장님", "부공장장님", "유대선", "이현조", "구상모", "주재근", "정태훈", "장광식", "박연주", "박득용", "이종주", "오현수", "이진원", "김성일", "이현준", "유보선", "남태율", "박석문", "박천용", "김문재", "주민수", "송일권", "최주용", "박노훈" ]

# --- [메뉴 1] 스코어 입력 ---
if menu == "📝 스코어 입력":
    st.title("⛳ 라운드 기록 입력")
    st.info("벌금 규정: 목표 대비 ±3타 이상 차이 발생 시 10,000원")
    
    with st.form(key="score_form"):
        c_date, c_place = st.columns(2)
        with c_date: date = st.date_input("날짜", datetime.now())
        with c_place: course = st.text_input("골프장명", value="힐데스하임 CC")

        st.divider()
        name = st.selectbox("본인 이름 선택", player_list)
        target = st.number_input("🎯 오늘의 목표 타수", 60, 120, 80)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: total = st.number_input("🏁 최종 총 타수", 60, 150, 85)
        with c2: birdies = st.number_input("🐤 버디 개수", 0, 18, 0)
        with c3: pars = st.number_input("✋ 파(Par) 개수", 0, 18, 0)
        with c4: bogeys = st.number_input("🌲 보기(Bogey) 개수", 0, 18, 0)

        submit = st.form_submit_button("기록 저장 및 벌금 확인")
        
        if submit:
            diff = total - target
            penalty = 10000 if abs(diff) >= 3 else 0
            
            new_entry = pd.DataFrame([{
                "날짜": date.strftime("%Y-%m-%d"),
                "골프장": course,
                "이름": name,
                "목표타수": target,
                "총타수": total,
                "버디": birdies, "파": pars, "보기": bogeys,
                "차이": diff, "벌금": penalty,
                "입력시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            
            # 구글 시트 누적 저장
            df = conn.read()
            updated_df = pd.concat([df, new_entry], ignore_index=True)
            conn.update(data=updated_df)
            
            st.success(f"✔️ {name}님, 저장 완료!")
            if penalty > 0:
                st.error(f"🚨 벌금 10,000원 당첨! (차이: {diff:+d}타)")
            else:
                st.balloons()

# --- [메뉴 2] 실시간 리더보드 ---
elif menu == "🏆 실시간 리더보드":
    st.title("📊 현재 라운드 순위")
    df = conn.read()
    today = datetime.now().strftime("%Y-%m-%d")
    td_df = df[df['날짜'] == today].sort_values(by="총타수")
    
    if not td_df.empty:
        st.dataframe(td_df[["이름", "총타수", "버디", "파", "보기", "벌금"]], use_container_width=True)
    else:
        st.write("오늘 입력된 데이터가 없습니다.")

# --- [메뉴 3] 오늘의 시상식 ---
elif menu == "🎁 오늘의 시상식":
    st.title("✨ 오늘의 주요 시상")
    df = conn.read()
    today = datetime.now().strftime("%Y-%m-%d")
    td = df[df['날짜'] == today]

    if not td.empty:
        m1, m2 = st.columns(2)
        medalist = td.loc[td['총타수'].idxmin()]
        m1.metric("🥇 메달리스트(최저타)", medalist['이름'], f"{medalist['총타수']}타")
        m2.metric("💰 오늘 모인 벌금 총액", f"{td['벌금'].sum():,}원")

        st.divider()
        st.subheader("🎖️ 부문별 다수 기록 시상")
        b1, b2, b3 = st.columns(3)
        
        with b1:
            st.markdown("### 🐤 다버디상")
            w = td.loc[td['버디'].idxmax()]
            if w['버디'] > 0: st.success(f"**{w['이름']}** ({w['버디']}개)")
            else: st.write("없음")

        with b2:
            st.markdown("### ✋ 다파상")
            w = td.loc[td['파'].idxmax()]
            if w['파'] > 0: st.info(f"**{w['이름']}** ({w['파']}개)")
            else: st.write("없음")

        with b3:
            st.markdown("### 🌲 다보기상")
            w = td.loc[td['보기'].idxmax()]
            if w['보기'] > 0: st.warning(f"**{w['이름']}** ({w['보기']}개)")
            else: st.write("없음")

        st.divider()
        st.subheader("💸 벌금 납부 명단")
        st.table(td[td['벌금'] > 0][["이름", "차이", "벌금"]])
    else:
        st.warning("데이터가 없습니다.")

# --- [메뉴 4] 누적 데이터 ---
elif menu == "📂 누적 데이터":
    st.title("📚 전체 라운드 히스토리")
    df = conn.read()
    st.dataframe(df.sort_values(by="날짜", ascending=False), use_container_width=True)
