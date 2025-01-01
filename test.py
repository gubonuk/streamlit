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
    crop_file = os.path.join(OUTPUT_FOLDER, f"{crop_name}.xlsx")

    if os.path.exists(crop_file):
        df = pd.read_excel(crop_file)
    else:
        combined_file_path = os.path.join(OUTPUT_FOLDER, COMBINED_FILE_NAME)
        if not os.path.exists(combined_file_path):
            return None
        df = pd.read_excel(combined_file_path)

    filtered_df = df[(df.iloc[:, 2] == crop_name) & (df.iloc[:, 3] == disease_name)]
    if filtered_df.empty:
        return None
    else:
        return filtered_df


st.title("작물 질병도감 및 농약 검색")

# 작물 질병도감 링크 조회
st.subheader("작물 질병도감")
crop_selection = st.selectbox("작물이름 선택:", [""] + list(crop_link_map.keys()))
if st.button("링크 열기"):
    if crop_selection:
        link = crop_link_map.get(crop_selection, None)
        if link:
            st.markdown(f"[{link}]({link})")
        else:
            st.write("해당 작물에 대한 링크 정보가 없습니다.")
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