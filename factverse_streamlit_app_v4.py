"""
팩트버스 (FactVerse) - Streamlit 프로토타입 (v3)

변경점:
- 문제 풀 12개 중 매 세션(새로고침)마다 6문제를 무작위로 출제
- 사이드바에 누적 포인트 + 기프티콘 교환 UI (실제 매장가와 동일한 포인트로 교환)
- 누적 포인트는 로컬 JSON 파일(factverse_wallet.json)에 저장돼 새로고침해도 유지됨
  (1인용 로컬 프로토타입 기준. 여러 사용자가 쓰려면 로그인 기반 DB가 필요함)

실행 방법:
    1) pip install streamlit
    2) streamlit run factverse_streamlit_app.py
"""

import json
import random
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="팩트버스 (FactVerse)", page_icon="🧭", layout="centered")

POINT_PER_CORRECT = 10
QUESTIONS_PER_SESSION = 6
WALLET_FILE = Path(__file__).parent / "factverse_wallet.json"

# ---------- 기프티콘: 실제 매장가와 동일한 포인트로 설정 ----------
GIFTICONS = [
    {"name": "컴포즈커피 카페라떼", "cost": 2900},
    {"name": "배스킨라빈스 싱글레귤러", "cost": 3900},
    {"name": "스타벅스 아메리카노(Tall)", "cost": 4700},
]

# ---------- 문제 풀: 2026년 7월 시사 뉴스 기반 12문항 (경제/문화/스포츠 각 4개) ----------
QUESTION_POOL = [
    # 경제
    {
        "category": "경제", "type": "ox",
        "article": "2026년 6월 소비자물가지수(CPI)가 발표됐다. 통계청에 따르면 6월 물가는 전월 대비 0.1%, 전년 동월 대비로는 3.2% 상승했다.",
        "question": "이 기사에 따르면, 최근 1년간 물가상승률은 3%를 넘었다.",
        "answer": "O",
        "explain": "전년 동월 대비 3.2% 상승했으니 3%를 넘은 게 맞아.",
        "source": "국가데이터처 / KDI 경제교육·정보센터 월간 경제이슈",
    },
    {
        "category": "경제", "type": "choice",
        "article": "SK하이닉스의 미국예탁증권(ADR)이 뉴욕증시에 상장되면서, 미국 시간 7월 13일 거래일부터 SK하이닉스 ADR 관련 레버리지 상품도 미국에서 거래될 전망이다.",
        "question": "이 기사를 가장 잘 요약한 선지는?",
        "options": [
            "SK하이닉스가 한국 증시에서 상장폐지됐다",
            "SK하이닉스 ADR이 미국 증시에 상장되고 관련 레버리지 상품 거래가 예정돼 있다",
            "SK하이닉스가 미국의 한 반도체 기업을 인수했다",
        ],
        "answer_idx": 1,
        "explain": "기사는 SK하이닉스 ADR의 미국 상장과 후속 레버리지 상품 거래 개시 예정을 전하고 있어.",
        "source": "한국경제TV 등 경제 뉴스",
    },
    {
        "category": "경제", "type": "ox",
        "article": "2026년 5월 온라인쇼핑 거래액이 25조130억원으로 집계됐다. 이는 전년 동월 대비 10.3% 증가한 수치다.",
        "question": "온라인쇼핑 거래액은 1년 전보다 10% 넘게 늘었다.",
        "answer": "O",
        "explain": "전년 동월 대비 10.3% 증가했으니 10%를 넘은 게 맞아.",
        "source": "국가데이터처 통계",
    },
    {
        "category": "경제", "type": "choice",
        "article": "OPEC+(석유수출국기구 플러스)가 8월 원유 생산량을 7월 대비 하루 18만8천 배럴 늘리기로 했다. 국제 유가에 영향을 줄 수 있는 조치다.",
        "question": "이 기사를 가장 잘 요약한 선지는?",
        "options": [
            "OPEC+가 8월부터 감산에 합의했다",
            "OPEC+가 8월 생산량을 늘리기로 했다",
            "OPEC+ 회원국들이 조직 해체를 논의 중이다",
        ],
        "answer_idx": 1,
        "explain": "기사의 핵심은 OPEC+의 8월 증산(하루 18만8천 배럴 확대) 결정이야.",
        "source": "Investing.com 경제 캘린더 등",
    },
    # 문화
    {
        "category": "문화", "type": "ox",
        "article": "서귀포 중문관광단지 인근의 한 로컬 티하우스가 7월부터 9월까지 운영시간을 기존 오후 5시 30분에서 오후 9시까지로 연장한다. 밤 시간대 즐길 거리가 부족하다는 지적에 따른 변화다.",
        "question": "이 매장은 여름 한정으로 운영시간을 오후 9시까지 늘렸다.",
        "answer": "O",
        "explain": "7~9월 한시적으로 마감 시간을 오후 9시까지 늦춘 게 맞아.",
        "source": "서울특별시 뉴스 / 제주 지역언론 보도 종합",
    },
    {
        "category": "문화", "type": "choice",
        "article": "서울시는 7월 한 달간 공연, 전시, 체험 등 다양한 문화행사를 운영한다. 다만 각 행사는 주최 기관 사정에 따라 변경되거나 취소될 수 있다.",
        "question": "이 기사를 가장 잘 요약한 선지는?",
        "options": [
            "서울시 문화행사가 7월에 전면 중단된다",
            "서울시가 7월에 다양한 문화행사를 운영하지만 일정은 바뀔 수 있다",
            "서울시 문화행사가 전부 유료로 전환됐다",
        ],
        "answer_idx": 1,
        "explain": "다양한 문화행사가 열리되, 주최 측 사정으로 변경·취소될 수 있다는 게 핵심이야.",
        "source": "서울특별시 뉴스(문화달력)",
    },
    {
        "category": "문화", "type": "ox",
        "article": "국립극장 공연예술박물관이 경기 파주 무대예술지원센터에서 기획전시 'STAGE: RE-PLAY'를 열고 있다. 이 전시는 7월 30일까지 시범 운영 후 8월 1일 정식 개막하며, 관람료는 무료다.",
        "question": "이 전시는 관람료를 받는다.",
        "answer": "X",
        "explain": "관람료는 무료라고 명시돼 있어.",
        "source": "국악신문(kukak21.com) 등 문화 뉴스",
    },
    {
        "category": "문화", "type": "choice",
        "article": "국립극장이 7월 3일부터 25일까지 하늘극장과 달오름극장에서 '2026 여우락 페스티벌'을 개최한다.",
        "question": "이 기사를 가장 잘 요약한 선지는?",
        "options": [
            "여우락 페스티벌이 8월에 새로 열린다",
            "여우락 페스티벌이 7월 3일부터 25일까지 국립극장에서 열린다",
            "여우락 페스티벌이 올해는 취소됐다",
        ],
        "answer_idx": 1,
        "explain": "7월 3일~25일, 국립극장 하늘/달오름극장에서 열린다는 게 핵심이야.",
        "source": "국립극장 공연 일정 보도",
    },
    # 스포츠
    {
        "category": "스포츠", "type": "ox",
        "article": "2026 FIFA 월드컵이 6월 11일 개막해 7월 19일 결승전으로 막을 내린다.",
        "question": "2026 월드컵 결승전은 7월 19일에 열린다.",
        "answer": "O",
        "explain": "6월 11일 개막, 7월 19일 결승으로 일정이 확정돼 있어.",
        "source": "FIFA 월드컵 일정 보도",
    },
    {
        "category": "스포츠", "type": "choice",
        "article": "메이저리그에서 뛰는 한 한국인 투수가 7월 들어서도 소속팀 콜업(1군 승격) 명단에 들지 못했다는 보도가 나왔다.",
        "question": "이 기사를 가장 잘 요약한 선지는?",
        "options": [
            "해당 선수가 메이저리그 올스타에 선정됐다",
            "해당 선수가 7월에도 1군에 올라오지 못했다",
            "해당 선수가 은퇴를 선언했다",
        ],
        "answer_idx": 1,
        "explain": "기사의 핵심은 7월에도 콜업(1군 승격)이 되지 않았다는 사실이야.",
        "source": "MLB 관련 국내 스포츠 매체 보도",
    },
    {
        "category": "스포츠", "type": "ox",
        "article": "메이저리그 뉴욕 양키스가 최근 7연패를 당했다. 이는 최근 3년 만의 일이라는 보도가 나왔다.",
        "question": "양키스는 최근 3년 만에 7연패를 당했다.",
        "answer": "O",
        "explain": "보도에 따르면 3년 만의 7연패가 맞아.",
        "source": "다음스포츠 해외야구 등",
    },
    {
        "category": "스포츠", "type": "choice",
        "article": "한국 축구의 미래를 새로 그리겠다는 취지의 'K-축구 혁신위원회'가 출범했다.",
        "question": "이 기사를 가장 잘 요약한 선지는?",
        "options": [
            "K-축구 혁신위원회가 해체를 선언했다",
            "한국 축구의 변화를 위한 혁신위원회가 새로 출범했다",
            "축구 국가대표팀 감독이 새로 선임됐다",
        ],
        "answer_idx": 1,
        "explain": "핵심은 한국 축구 혁신을 위한 위원회가 새로 출범했다는 사실이야.",
        "source": "스포츠경향 등 축구 관련 보도",
    },
]

# ---------- 지갑(누적 포인트) 파일 입출력 ----------
def load_wallet():
    if WALLET_FILE.exists():
        try:
            return json.loads(WALLET_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"total_points": 0, "redeemed": []}

def save_wallet(wallet):
    WALLET_FILE.write_text(json.dumps(wallet, ensure_ascii=False, indent=2), encoding="utf-8")

# 매 스크립트 실행(=매 상호작용)마다 디스크에서 다시 읽어와, 사이드바 값이 항상 최신 저장값과 일치하도록 함
st.session_state.wallet = load_wallet()

# ---------- 세션 상태 초기화 (새로고침 시 여기서부터 다시 시작 → 문제도 새로 뽑힘) ----------
if "screen" not in st.session_state:
    st.session_state.screen = "intro"
    st.session_state.session_quiz = random.sample(QUESTION_POOL, QUESTIONS_PER_SESSION)
    st.session_state.q_idx = 0
    st.session_state.session_points = 0
    st.session_state.correct = 0
    st.session_state.answered = False
    st.session_state.last_choice = None

def goto(screen):
    st.session_state.screen = screen

def reset_all():
    st.session_state.screen = "intro"
    st.session_state.session_quiz = random.sample(QUESTION_POOL, QUESTIONS_PER_SESSION)
    st.session_state.q_idx = 0
    st.session_state.session_points = 0
    st.session_state.correct = 0
    st.session_state.answered = False
    st.session_state.last_choice = None

def add_points(n):
    st.session_state.session_points += n
    st.session_state.wallet["total_points"] += n
    save_wallet(st.session_state.wallet)

st.markdown(
    "<style>.block-container{max-width:520px;padding-top:2rem;} "
    "div.stButton>button{width:100%;border-radius:10px;height:3em;font-size:1.02em;}</style>",
    unsafe_allow_html=True,
)

# ---------- 사이드바: 누적 포인트 + 기프티콘 교환 ----------
with st.sidebar:
    st.header("💰 내 포인트")
    st.metric("누적 포인트", f"{st.session_state.wallet['total_points']} P")
    st.caption("포인트는 새로고침해도 유지돼요 (로컬 저장).")
    st.divider()
    st.subheader("🎁 기프티콘 교환")
    for i, g in enumerate(GIFTICONS):
        already = g["name"] in st.session_state.wallet["redeemed"]
        st.write(f"**{g['name']}** — {g['cost']} P")
        can_redeem = st.session_state.wallet["total_points"] >= g["cost"] and not already
        label = "✅ 교환 완료" if already else "교환하기"
        if st.button(label, key=f"side_redeem_{i}", disabled=not can_redeem or already):
            st.session_state.wallet["total_points"] -= g["cost"]
            st.session_state.wallet["redeemed"].append(g["name"])
            save_wallet(st.session_state.wallet)
            st.rerun()
        if not can_redeem and not already:
            need = g["cost"] - st.session_state.wallet["total_points"]
            st.caption(f"{need}P 더 필요해요")
        st.write("")

st.title("🧭 팩트버스 (FactVerse)")
st.caption("메타버스 안에서 시사 뉴스를 읽고, 팩트체크하며 포인트를 모아보세요")
st.divider()

# ---------- 화면 1: 인트로 ----------
if st.session_state.screen == "intro":
    st.subheader("경제 · 문화 · 스포츠 뉴스로 팩트체크 습관 기르기")
    st.write(
        "알파세대는 SNS보다 메타버스를 더 많이 이용해요. "
        "팩트버스는 그 메타버스 공간 안에서 짧은 시사 뉴스를 읽고, "
        "OX 판단이나 요약 선지 고르기로 팩트체크 습관을 길러요."
    )
    st.write(f"오늘의 퀴즈는 총 {QUESTIONS_PER_SESSION}문제, 문제당 정답 시 {POINT_PER_CORRECT}포인트를 받아요.")
    st.write("새로고침할 때마다 다른 뉴스로 새 퀴즈가 나와요.")
    if st.button("시작하기 ▶"):
        goto("quiz")
        st.rerun()

# ---------- 화면 2: 퀴즈 ----------
elif st.session_state.screen == "quiz":
    idx = st.session_state.q_idx
    total = len(st.session_state.session_quiz)

    if idx >= total:
        goto("result")
        st.rerun()

    item = st.session_state.session_quiz[idx]
    st.progress(idx / total, text=f"{idx + 1} / {total} 문제 · {item['category']}")
    st.markdown(f"**[{item['category']}]** {item['article']}")
    st.markdown(f"### ❓ {item['question']}")

    if not st.session_state.answered:
        if item["type"] == "ox":
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⭕ O (참)"):
                    st.session_state.last_choice = "O"
                    st.session_state.answered = True
                    if item["answer"] == "O":
                        add_points(POINT_PER_CORRECT)
                        st.session_state.correct += 1
                    st.rerun()
            with col2:
                if st.button("❌ X (거짓)"):
                    st.session_state.last_choice = "X"
                    st.session_state.answered = True
                    if item["answer"] == "X":
                        add_points(POINT_PER_CORRECT)
                        st.session_state.correct += 1
                    st.rerun()
        else:  # choice
            for i, opt in enumerate(item["options"]):
                if st.button(f"{chr(65+i)}. {opt}", key=f"opt_{idx}_{i}"):
                    st.session_state.last_choice = i
                    st.session_state.answered = True
                    if i == item["answer_idx"]:
                        add_points(POINT_PER_CORRECT)
                        st.session_state.correct += 1
                    st.rerun()
    else:
        if item["type"] == "ox":
            is_correct = st.session_state.last_choice == item["answer"]
            correct_label = item["answer"]
        else:
            is_correct = st.session_state.last_choice == item["answer_idx"]
            correct_label = f"{chr(65+item['answer_idx'])}. {item['options'][item['answer_idx']]}"

        if is_correct:
            st.success(f"정답이에요! +{POINT_PER_CORRECT}포인트 획득 🎉")
        else:
            st.error(f"아쉬워요. 정답은 {correct_label} 이었어요.")
        st.info(item["explain"])
        st.caption(f"출처: {item['source']}")

        if st.button("다음 문제 ▶" if idx + 1 < total else "결과 보기 ▶"):
            st.session_state.q_idx += 1
            st.session_state.answered = False
            st.session_state.last_choice = None
            st.rerun()

# ---------- 화면 3: 결과 ----------
elif st.session_state.screen == "result":
    st.subheader("🎉 퀴즈 완료!")
    st.metric("이번 세션 정답 수", f"{st.session_state.correct} / {len(st.session_state.session_quiz)}")
    st.metric("이번 세션 획득 포인트", f"{st.session_state.session_points} P")
    st.metric("누적 포인트", f"{st.session_state.wallet['total_points']} P")
    st.write("사이드바에서 기프티콘으로 교환할 수 있어요.")
    if st.button("처음부터 다시하기 ↺"):
        reset_all()
        st.rerun()
