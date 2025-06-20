import json

import streamlit as st

st.title("📊 JSON 문자열 비교 도구 (한 줄 비교 시 보기 좋게)")

st.markdown("두 개의 JSON 파일을 업로드하세요. 공통 키를 찾아 각 항목의 문자열을 비교합니다.")

# 파일 업로드
file1 = st.file_uploader("🔼 첫 번째 JSON 업로드", type=["json"], key="file1")
file2 = st.file_uploader("🔼 두 번째 JSON 업로드", type=["json"], key="file2")

if file1 and file2:
    try:
        json1 = json.load(file1)
        json2 = json.load(file2)

        # 공통 키 추출
        common_keys = set(json1.keys()) & set(json2.keys())

        if not common_keys:
            st.warning("두 JSON 파일에 공통된 최상위 키가 없습니다.")
        else:
            selected_key = st.selectbox("🔑 비교할 공통 키를 선택하세요", sorted(common_keys))

            dict1 = json1[selected_key]
            dict2 = json2[selected_key]

            if set(dict1.keys()) != set(dict2.keys()):
                st.error(f"선택된 키('{selected_key}')의 내부 key 수가 다릅니다. 비교할 수 없습니다.")
            else:
                st.success(f"'{selected_key}' 항목의 {len(dict1)}개 데이터를 비교합니다.")

                for sub_key in sorted(dict1.keys(), key=lambda x: int(x) if x.isdigit() else x):
                    st.markdown(f"### 🔹  {int(sub_key)} ~ {int(sub_key) + 2} minutes")
                    st.markdown("**File 1:**")
                    st.markdown(f"> {dict1[sub_key].strip().replace('\n', '  \n')}")
                    st.markdown("**File 2:**")
                    st.markdown(f"> {dict2[sub_key].strip().replace('\n', '  \n')}")
                    st.markdown("---")

    except json.JSONDecodeError:
        st.error("JSON 파일 형식이 올바르지 않습니다.")
