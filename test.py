import os
import pandas as pd
import streamlit as st
import webbrowser

# 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")  # Excel 파일들이 있는 폴더 (미리 존재한다고 가정)
COMBINED_FILE_NAME = "기타작물.xlsx"
CROPLINK_FILE = os.path.join(BASE_DIR, "croplinkmobile.txt")

# croplink.txt 읽어서 {작물명: URL} 딕셔너리 만들기
crop_link_map = {}
if os.path.exists(CROPLINK_FILE):
    with open(CROPLINK_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "://" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    crop_name = parts[0].strip()
                    url = parts[1].strip()
                    crop_link_map[crop_name] = url


def search_pesticide(crop_name, disease_name):
    # 엑셀 파일 결정
    crop_file = os.path.join(OUTPUT_FOLDER, f"{crop_name}.xlsx")
    if os.path.exists(crop_file):
        df = pd.read_excel(crop_file)
    else:
        combined_file = os.path.join(OUTPUT_FOLDER, COMBINED_FILE_NAME)
        if not os.path.exists(combined_file):
            return None
        df = pd.read_excel(combined_file)

    # 실제 엑셀 파일에 들어있는 컬럼명 확인
    # st.write(df.columns)  # 디버깅용

    # --------------------------------------------------------
    # 1) 필요하다면 header 옵션을 조정 (header=0 또는 header=None 등)
    #    df = pd.read_excel(..., header=0)
    #
    # 2) "Unnamed: 2" 등을 우리가 원하는 최종 컬럼명으로 rename
    #    예시: 3번째 컬럼 -> "작물명", 4번째 컬럼 -> "적용병해충"
    # --------------------------------------------------------
    df = df.rename(columns={
        "농약제품목록": "번호",
        "Unnamed: 1": "등록번호",
        "Unnamed: 2": "작물명",         # 3번째 열
        "Unnamed: 3": "적용병해충",     # 4번째 열
        "Unnamed: 4": "품목명",
        "Unnamed: 5": "일반명",
        "Unnamed: 6": "주성분함량",
        "Unnamed: 7": "상표명",
        "Unnamed: 8": "인축독성",
        "Unnamed: 9": "어독성",
        "Unnamed: 10": "용도",
        "Unnamed: 11": "등록일",
        "Unnamed: 12": "작용기작",
        "Unnamed: 13": "희석배수",
        "Unnamed: 14": "사용량",
        "Unnamed: 15": "사용적기",
        "Unnamed: 16": "사용방법",
        "Unnamed: 17": "안전사용시기",
        "Unnamed: 18": "안전사용횟수",
        "Unnamed: 19": "제형",
        "Unnamed: 20": "회사명",
        # 만약 마지막 "작물명" 열이 정말 다른 정보라면 중복 피하려고 이름 변경
        "작물명": "작물명2"    # 실제로는 어떤 정보인지 확인 후 적절히 수정
    })

    # 공백 제거 (Series 전체에 대해)
    df["작물명"] = df["작물명"].astype(str).str.strip()
    df["적용병해충"] = df["적용병해충"].astype(str).str.strip()

    # 부분 일치 검색
    filtered_df = df[
        df["작물명"].str.contains(crop_name, na=False) &
        df["적용병해충"].str.contains(disease_name, na=False)
    ]

    if filtered_df.empty:
        return None

    return filtered_df


# ------------------- Streamlit 앱 -------------------
st.title("작물 질병도감 및 농약 검색")

# 작물 질병도감 링크 조회
st.subheader("작물 질병도감")
crop_selection = st.selectbox("작물이름 선택:", [""] + list(crop_link_map.keys()))
if st.button("링크 열기"):
    if crop_selection:
        link = crop_link_map.get(crop_selection)
        if link:
            st.markdown(f"[{link}]({link})")
        else:
            st.write("해당 작물에 대한 링크가 없습니다.")
    else:
        st.write("작물명을 선택하세요.")

# 농약 검색
st.subheader("농약 검색")
crop_name_input = st.text_input("작물이름")
disease_name_input = st.text_input("병해명")

if st.button("검색"):
    if not crop_name_input or not disease_name_input:
        st.write("작물명과 병명을 모두 입력하세요.")
    else:
        result = search_pesticide(crop_name_input, disease_name_input)
        if result is None or result.empty:
            st.write("검색 결과 없음")
        else:
            st.dataframe(result)
