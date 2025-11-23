import streamlit as st
from custom_csv_parser.dataframe import DataFrame
from custom_csv_parser.csv_parser import CSVParser
import os

# --- Page Config ---
st.set_page_config(page_title="Grouping and Aggregation", page_icon="📊", layout="wide")

st.title("📊 Grouping and Aggregation")
st.markdown(
    """
This page demonstrates the **Split-Apply-Combine** strategy. 
You can group data by a categorical column (Split) and apply summary functions (Apply) to produce a new table (Combine).
"""
)

# --- File Paths ---
DATA_DIR = "data"
TMP_DIR = os.path.join(DATA_DIR, "tmp")
if not os.path.exists(TMP_DIR):
    os.makedirs(TMP_DIR)

AVAILABLE_FILES = {
    "Donor Metadata": os.path.join(DATA_DIR, "sea-ad_cohort_donor_metadata_072524.csv"),
    "MRI Volumetrics": os.path.join(DATA_DIR, "sea-ad_cohort_mri_volumetrics.csv"),
    "Neuropathology": os.path.join(
        DATA_DIR, "sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv"
    ),
    "Cognitive Scores": os.path.join(
        DATA_DIR, "sea-ad_cohort_harmonized_cognitive_scores_20241213.csv"
    ),
}

# --- 1. Select Data Source ---
st.header("Step 1: Select Dataset")

data_source = st.radio(
    "Data Source:", ["Preset Datasets", "Upload Custom CSV"], horizontal=True
)

file_path = None
selected_df_name = None

if data_source == "Preset Datasets":
    selected_df_name = st.selectbox("Choose a dataset:", list(AVAILABLE_FILES.keys()))
    file_path = AVAILABLE_FILES[selected_df_name]

elif data_source == "Upload Custom CSV":
    uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
    if uploaded_file is not None:
        file_path = os.path.join(TMP_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        selected_df_name = uploaded_file.name
        st.success(f"File uploaded successfully: {selected_df_name}")
    else:
        st.info("Please upload a CSV file to proceed.")
        st.stop()


# --- Load Data ---
@st.cache_data(show_spinner=False)
def load_data(path):
    try:
        return CSVParser(filepath=path).parse()
    except Exception as e:
        st.error(f"Error parsing file: {e}")
        return None


if file_path:
    df = load_data(file_path)

    if df is None:
        st.stop()

    st.info(f"Loaded **{selected_df_name}** ({df._shape[0]} rows).")
    with st.expander("View Raw Data"):
        st.dataframe(df.head(5).to_dict())

    # --- 2. Configure Grouping ---
    st.header("Step 2: Configure Group By")

    if not df._columns:
        st.error("The dataset has no columns.")
        st.stop()

    # 2a. Select Grouping Column
    group_col = st.selectbox(
        "Select column to Group By (The 'Split' step):",
        options=df._columns,
        help="Rows with the same value in this column will be bundled together.",
    )

    # 2b. Configure Aggregations
    st.subheader("Configure Aggregations (The 'Apply' step)")

    if "agg_rules" not in st.session_state:
        st.session_state.agg_rules = []

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        target_col = st.selectbox("Column to Aggregate:", options=df._columns)
    with col2:
        agg_func = st.selectbox("Function:", options=["count", "mean", "max", "min"])
    with col3:
        st.write("")
        st.write("")
        if st.button("Add Rule"):
            if (target_col, agg_func) not in st.session_state.agg_rules:
                st.session_state.agg_rules.append((target_col, agg_func))

    # --- LIMITATION NOTE ---
    st.warning(
        "⚠️ **Note on Multiple Aggregations:** "
        "This custom engine currently supports only **one aggregation rule per column**. "
        "If you add multiple rules for the same column, the most recent rule will overwrite the previous ones."
    )

    if st.session_state.agg_rules:
        st.markdown("**Current Aggregation Rules:**")
        agg_dict = {}
        for i, (col, func) in enumerate(st.session_state.agg_rules):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.code(f"{func}({col})")
            with c2:
                if st.button("❌", key=f"del_{i}"):
                    st.session_state.agg_rules.pop(i)
                    st.rerun()
            agg_dict[col] = func
    else:
        st.info("Please add at least one aggregation rule.")
        agg_dict = {}

    # --- 3. Execute ---
    st.header("Step 3: Result")

    if st.button("Apply Grouping & Aggregation", type="primary", disabled=not agg_dict):
        try:
            grouped_df = df.groupby(group_col)
            result_df = grouped_df.agg(agg_dict)

            st.success("Grouping successful!")
            st.dataframe(result_df.to_dict())
            st.write(f"Result shape: {result_df._shape[0]} groups found.")

        except Exception as e:
            st.error(f"An error occurred during aggregation: {e}")
