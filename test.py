import os
import pandas as pd
import streamlit as st
import webbrowser

# st_aggrid 설치 필요
# pip install streamlit-aggrid
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# 1) 파일 경로 설정 (원래 코드 그대로)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")  # Excel 파일들이 있는 폴더 (미리 존재한다고 가정)
COMBINED_FILE_NAME = "기타작물.xlsx"
CROPLINK_FILE = os.path.join(BASE_DIR, "croplinkmobile.txt")

# croplink.txt 읽어서 {작물명: URL} 딕셔너리 (원래 코드 그대로)
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

# 2) search_pesticide 함수 (원래 코드 + 열 매핑)
def search_pesticide(crop_name, disease_name):
    crop_file = os.path.join(OUTPUT_FOLDER, f"{crop_name}.xlsx")
    if os.path.exists(crop_file):
        df = pd.read_excel(crop_file)
    else:
        combined_file = os.path.join(OUTPUT_FOLDER, COMBINED_FILE_NAME)
        if not os.path.exists(combined_file):
            return None
        df = pd.read_excel(combined_file)

    # 원래 열 이름 재매핑
    df = df.rename(columns={
        "농약제품목록": "번호",
        "Unnamed: 1": "등록번호",
        "Unnamed: 2": "작물명",         
        "Unnamed: 3": "적용병해충",     
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
        # 만약 마지막 "작물명" 열이 중복이라면 중복 방지
        "작물명": "작물명2"
    })

    # 공백 제거
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

# 3) Streamlit 앱
st.set_page_config(layout="wide")
st.title("작물 질병도감 및 농약 검색 - (더블클릭 디버깅)")

# 작물 질병도감 링크 조회
st.subheader("작물 질병도감")
crop_selection = st.selectbox("작물이름 선택:", [""] + list(crop_link_map.keys()))
if st.button("링크 열기"):
    if crop_selection:
        link = crop_link_map.get(crop_selection)
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

search_button = st.button("검색")

if search_button:
    if not crop_name_input or not disease_name_input:
        st.write("작물명과 병명을 모두 입력하세요.")
    else:
        result = search_pesticide(crop_name_input, disease_name_input)
        if result is None or result.empty:
            st.write("검색 결과 없음")
        else:
            st.write("검색 결과 (행을 더블클릭하면 확인)")

            # ─────────────── st_aggrid (onRowDoubleClicked) ───────────────
            gb = GridOptionsBuilder.from_dataframe(result)

            # JS 콜백: 행 더블클릭 시 alert + console.log
            custom_js = """
            function(e) {
                alert("DoubleClick row: " + JSON.stringify(e.data));
                console.log("DoubleClick rowData:", e.data);

                window.postMessage({
                    'type': 'ROW_DOUBLE_CLICK',
                    'rowData': e.data
                }, '*');
            }
            """

            gb.configure_grid_options(
                onRowDoubleClicked=custom_js,
                rowSelection='single',
                suppressRowClickSelection=True
            )

            grid_opts = gb.build()
            grid_response = AgGrid(
                result,
                gridOptions=grid_opts,
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.NO_UPDATE,
                allow_unsafe_jscode=True,
                height=600,
                use_container_width=True
            )

            st.write("--- [Debug] grid_response ---")
            st.write(grid_response)

            # 더블클릭된 행이 selected_rows 로 들어오는지 확인
            sel_rows = grid_response.get("selected_rows", [])
            if sel_rows:
                st.write("**더블클릭된 행**:", sel_rows[-1])
            else:
                st.write("아직 더블클릭된 행이 없습니다 (팝업, 콘솔로그도 확인).")
