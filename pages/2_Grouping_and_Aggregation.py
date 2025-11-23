import streamlit as st
from custom_csv_parser.csv_parser import CSVParser
import os

# --- Page Config ---
st.set_page_config(page_title="Grouping and Aggregation", page_icon="📊", layout="wide")

st.title("📊 Grouping and Aggregation")
st.markdown(
    """
This page lets you interactively test the **Grouping** and **Aggregation** capabilities on the **individual** datasets.
You can group data by a categorical column (Split) and apply summary functions (Apply) to produce a new table (Combine).
"""
)

# --- File Paths ---
DATA_DIR = "data"
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

# --- 1. Load Data ---
st.header("Step 1: Select Dataset")
selected_df_name = st.selectbox("Choose a dataset:", AVAILABLE_FILES.keys())


@st.cache_data(show_spinner=False)
def load_data(path):
    return CSVParser(filepath=path).parse()


file_path = AVAILABLE_FILES[selected_df_name]
try:
    df = load_data(file_path)
    st.info(f"Loaded **{selected_df_name}** ({df._shape[0]} rows).")
    with st.expander("View Raw Data"):
        st.dataframe(df.head(5).to_dict())
except Exception as e:
    st.error(f"Error loading file: {e}")
    st.stop()

# --- 2. Configure Grouping ---
st.header("Step 2: Configure Group By")

# 2a. Select Grouping Column
group_col = st.selectbox(
    "Select column to Group By (The 'Split' step):",
    options=df._columns,
    help="Rows with the same value in this column will be bundled together.",
)

# 2b. Configure Aggregations
st.subheader("Configure Aggregations (The 'Apply' step)")

# Session state to hold the aggregation rules
if "agg_rules" not in st.session_state:
    st.session_state.agg_rules = []

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    target_col = st.selectbox("Column to Aggregate:", options=df._columns)
with col2:
    agg_func = st.selectbox("Function:", options=["count", "mean", "max", "min"])
with col3:
    # Spacer to align button
    st.write("")
    st.write("")
    if st.button("Add Rule"):
        # Prevent duplicate rules for the same column + function
        if (target_col, agg_func) not in st.session_state.agg_rules:
            st.session_state.agg_rules.append((target_col, agg_func))

# --- LIMITATION NOTE ---
st.warning(
    "⚠️ **Note on Multiple Aggregations:** "
    "This custom engine currently supports only **one aggregation rule per column**. "
    "If you add multiple rules for the same column (e.g., 'Age: mean' and 'Age: max'), "
    "the most recent rule will overwrite the previous ones. "
    "\n\n**Reason:** The backend `agg()` method accepts a Python dictionary `{column: function}`, "
    "which inherently enforces unique keys."
)

# Display current rules
if st.session_state.agg_rules:
    st.markdown("**Current Aggregation Rules:**")

    # Prepare the dictionary for the backend
    agg_dict = {}

    for i, (col, func) in enumerate(st.session_state.agg_rules):
        c1, c2 = st.columns([4, 1])
        with c1:
            st.code(f"{func}({col})")
        with c2:
            if st.button("❌", key=f"del_{i}"):
                st.session_state.agg_rules.pop(i)
                st.rerun()

        # Add to the dictionary used for the actual calculation
        agg_dict[col] = func
else:
    st.info("Please add at least one aggregation rule.")
    agg_dict = {}

# --- 3. Execute ---
st.header("Step 3: Result")

if st.button("Apply Grouping & Aggregation", type="primary", disabled=not agg_dict):
    try:
        # 1. Group By
        grouped_df = df.groupby(group_col)

        # 2. Aggregation
        result_df = grouped_df.agg(agg_dict)

        st.success("Grouping successful!")
        st.dataframe(result_df.to_dict())

        st.write(f"Result shape: {result_df._shape[0]} groups found.")

    except Exception as e:
        st.error(f"An error occurred during aggregation: {e}")
