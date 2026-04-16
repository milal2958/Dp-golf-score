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

# ==========================================
# [메뉴 1] 스코어 입력 (이름 직접 입력 기능 반영)
# ==========================================
if menu == "📝 스코어 입력":
    st.title("⛳ 라운드 기록 입력")
    st.info("💡 벌금 규정: 목표 대비 ±3타 이상 차이 발생 시 10,000원")
    
    with st.form(key="score_form"):
        c_date, c_place = st.columns(2)
        with c_date: date = st.date_input("날짜", datetime.now())
        with c_place: course = st.text_input("골프장명", value="힐데스하임 CC")

        st.divider()
        
        # 이름 직접 입력 (placeholder로 안내 문구 추가)
        name = st.text_input("👤 본인 이름 입력", placeholder="이름 또는 닉네임을 입력하세요")
        
        target = st.number_input("🎯 오늘의 목표 타수", min_value=60, max_value=120, value=80)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: total = st.number_input("🏁 최종 총 타수", min_value=60, max_value=150, value=85)
        with c2: birdies = st.number_input("🐤 버디 개수", min_value=0, max_value=18, value=0)
        with c3: pars = st.number_input("✋ 파(Par) 개수", min_value=0, max_value=18, value=0)
        with c4: bogeys = st.number_input("🌲 보기(Bogey) 개수", min_value=0, max_value=18, value=0)

        submit = st.form_submit_button("기록 저장 및 벌금 확인")
        
        if submit:
            # 이름이 비어있는지 확인하는 방어 로직
            if not name.strip():
                st.warning("⚠️ 이름을 반드시 입력해 주세요!")
            else:
                # 1. 타수 차이 및 벌금 계산
                diff = total - target
                penalty = 10000 if abs(diff) >= 3 else 0
                
                # 2. 저장할 새로운 행 데이터 생성
                new_entry = pd.DataFrame([{
                    "날짜": date.strftime("%Y-%m-%d"),
                    "골프장": course,
                    "이름": name.strip(), # 앞뒤 공백 제거 후 저장
                    "목표타수": target,
                    "총타수": total,
                    "버디": birdies, "파": pars, "보기": bogeys,
                    "차이": diff, "벌금": penalty,
                    "입력시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])
                
                try:
                    # 3. ttl=0으로 최신 데이터를 무조건 다시 읽어옴 (캐시 무시)
                    existing_df = conn.read(ttl=0)
                    
                    # 4. 기존 데이터 뒤에 새 데이터 붙이기 (누적 저장)
                    updated_df = pd.concat([existing_df, new_entry], ignore_index=True)
                    
                    # 5. 전체 데이터를 시트에 다시 쓰기
                    conn.update(data=updated_df)
                    
                    st.success(f"✔️ {name}님, {len(updated_df)}번째 기록으로 안전하게 저장되었습니다!")
                    
                    # 6. 벌금 결과 알림
                    if penalty > 0:
                        st.error(f"🚨 벌금 10,000원 당첨! (차이: {diff:+d}타)")
                    else:
                        st.balloons()
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다. 권한 설정을 확인하세요: {e}")

# ==========================================
# [메뉴 2] 실시간 리더보드
# ==========================================
elif menu == "🏆 실시간 리더보드":
    st.title("📊 현재 라운드 순위")
    df = conn.read(ttl=0)
    today = datetime.now().strftime("%Y-%m-%d")
    
    td_df = df[df['날짜'] == today].sort_values(by="총타수")
    
    if not td_df.empty:
        display_cols = ["이름", "총타수", "차이", "버디", "파", "보기", "벌금"]
        st.dataframe(td_df[display_cols], use_container_width=True)
    else:
        st.info("오늘 입력된 데이터가 없습니다.")

# ==========================================
# [메뉴 3] 오늘의 시상식 (다버디, 다파, 다보기)
# ==========================================
elif menu == "🎁 오늘의 시상식":
    st.title("✨ 오늘의 주요 시상")
    df = conn.read(ttl=0)
    today = datetime.now().strftime("%Y-%m-%d")
    td = df[df['날짜'] == today]

    if not td.empty:
        m1, m2 = st.columns(2)
        medalist = td.loc[td['총타수'].idxmin()]
        m1.metric("🥇 메달리스트(최저타)", medalist['이름'], f"{medalist['총타수']}타")
        
        total_penalty = td['벌금'].sum()
        m2.metric("💰 오늘 모인 벌금 총액", f"{total_penalty:,}원")

        st.divider()
        st.subheader("🎖️ 부문별 다수 기록 시상")
        b1, b2, b3 = st.columns(3)
        
        with b1:
            st.markdown("### 🐤 다버디상")
            w = td.loc[td['버디'].idxmax()]
            if w['버디'] > 0: 
                st.success(f"**{w['이름']}** ({w['버디']}개)")
            else: 
                st.write("대상자 없음")

        with b2:
            st.markdown("### ✋ 다파상")
            w = td.loc[td['파'].idxmax()]
            if w['파'] > 0: 
                st.info(f"**{w['이름']}** ({w['파']}개)")
            else: 
                st.write("대상자 없음")

        with b3:
            st.markdown("### 🌲 다보기상")
            w = td.loc[td['보기'].idxmax()]
            if w['보기'] > 0: 
                st.warning(f"**{w['이름']}** ({w['보기']}개)")
            else: 
                st.write("대상자 없음")

        st.divider()
        st.subheader("💸 벌금 납부 명단")
        penalty_list = td[td['벌금'] > 0][["이름", "차이", "벌금"]]
        
        if not penalty_list.empty:
            st.table(penalty_list)
        else:
            st.write("오늘 벌금 대상자가 없습니다! 다들 훌륭한 라운딩을 하셨네요.")
    else:
        st.warning("데이터가 없습니다. 스코어를 먼저 입력해 주세요.")

# ==========================================
# [메뉴 4] 누적 데이터
# ==========================================
elif menu == "📂 누적 데이터":
    st.title("📚 전체 라운드 히스토리")
    df = conn.read(ttl=0)
    
    if not df.empty:
        st.dataframe(df.sort_values(by="입력시간", ascending=False), use_container_width=True)
    else:
        st.info("아직 누적된 데이터가 없습니다.")