import streamlit as st
import requests
import json
from typing import Dict, List
import pandas as pd

# Configure the page
st.set_page_config(page_title="Drug Information Search", page_icon="💊", layout="wide")

# Constants
API_BASE_URL = "http://localhost:8000/api/v1"


def search_drug(drug_name: str) -> Dict:
    """Search for drug information using the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/drugs/{drug_name}/indications")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching drug information: {str(e)}")
        return None


def display_drug_info(drug_data: Dict):
    """Display drug information in a structured format."""
    if not drug_data:
        return

    st.header(f"💊 {drug_data['drug']}")

    # Create columns for layout
    col1, col2 = st.columns([2, 1])
    with col1:

        # Display indication
        if drug_data.get("indication"):
            st.subheader("Indication")
            with st.container(border=True, height=200):
                st.write(drug_data["indication"]["original_text"])

            # Display ICD-10 codes in a table
            if drug_data["indication"].get("icd10_codes"):
                st.subheader("ICD-10 Codes")
                icd_data = []
                for icd in drug_data["indication"]["icd10_codes"]:
                    icd_data.append(
                        {
                            "Code": icd["code"],
                            "Description": icd["description"],
                            "Category": icd["category"],
                            "Confidence Score": f"{icd['confidence_score']:.2f}",
                        }
                    )

                st.dataframe(
                    pd.DataFrame(icd_data).sort_values(
                        by="Confidence Score", ascending=False
                    ),
                    use_container_width=True,
                    hide_index=True,
                    column_order=[
                        "Code",
                        "Description",
                        "Category",
                        "Confidence Score",
                    ],
                )

    with col2:
        # Display directions if available
        if drug_data.get("directions"):
            st.subheader("Directions")
            with st.container(border=True, height=200):
                st.write(drug_data["directions"])


def main():
    st.title("Drug Information Search")
    st.write(
        "Search for drug information including indications, ICD-10 codes, and directions."
    )

    # Search input
    drug_name = st.text_input("Enter drug name:", placeholder="e.g., FOCALINXR")

    if drug_name:
        with st.spinner("Searching for drug information..."):
            drug_data = search_drug(drug_name)
            display_drug_info(drug_data)


if __name__ == "__main__":
    main()
