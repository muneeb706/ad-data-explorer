import streamlit as st
from custom_csv_parser.csv_parser import CSVParser
import os

# --- Page Config ---
st.set_page_config(page_title="Join Datasets", page_icon="🔗", layout="wide")

st.title("🔗 Join Datasets")
st.markdown(
    """
This page demonstrates the **Hash Join** algorithm implemented in the custom engine.
You can combine two datasets horizontally based on a common key column (e.g., `Donor ID`).
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


@st.cache_data(show_spinner=False)
def load_data(path):
    return CSVParser(filepath=path).parse()


# --- 1. Select Datasets ---
st.header("Step 1: Select Datasets")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Left Dataset")
    left_name = st.selectbox(
        "Choose Left Dataset:", list(AVAILABLE_FILES.keys()), index=0
    )
    try:
        left_df = load_data(AVAILABLE_FILES[left_name])
        st.info(f"Loaded: {left_df._shape[0]} rows, {left_df._shape[1]} cols")
        with st.expander("View Left Data"):
            st.dataframe(left_df.head(3).to_dict())
    except Exception as e:
        st.error(f"Error loading left file: {e}")
        st.stop()

with col2:
    st.subheader("Right Dataset")
    # Default to second file to make it easy to join immediately
    right_name = st.selectbox(
        "Choose Right Dataset:", list(AVAILABLE_FILES.keys()), index=1
    )
    try:
        right_df = load_data(AVAILABLE_FILES[right_name])
        st.info(f"Loaded: {right_df._shape[0]} rows, {right_df._shape[1]} cols")
        with st.expander("View Right Data"):
            st.dataframe(right_df.head(3).to_dict())
    except Exception as e:
        st.error(f"Error loading right file: {e}")
        st.stop()

# --- 2. Configure Join Keys ---
st.header("Step 2: Configure Join Keys")

# Find common columns to suggest as default
common_cols = list(set(left_df._columns) & set(right_df._columns))
default_index = 0
if "Donor ID" in common_cols:
    default_index = common_cols.index("Donor ID")
elif common_cols:
    default_index = 0
else:
    default_index = 0

col1, col2 = st.columns(2)
with col1:
    left_on = st.selectbox(
        "Left Key Column:",
        left_df._columns,
        index=(
            left_df._columns.index("Donor ID") if "Donor ID" in left_df._columns else 0
        ),
    )
with col2:
    right_on = st.selectbox(
        "Right Key Column:",
        right_df._columns,
        index=(
            right_df._columns.index("Donor ID")
            if "Donor ID" in right_df._columns
            else 0
        ),
    )

# --- 3. Execute Join ---
st.header("Step 3: Result")

# --- LIMITATION NOTE ---
st.warning(
    "⚠️ **Note on Join Type:** "
    "This custom engine currently supports only **Inner Join**. "
    "Rows that do not have matching keys in both datasets will be excluded from the result."
)

if st.button("Execute Inner Join", type="primary"):
    try:
        with st.spinner("Joining datasets..."):
            # Call the custom join method
            joined_df = left_df.join(right_df, left_on=left_on, right_on=right_on)

        st.success("Join successful!")

        # Display Stats
        st.write(
            f"**Left Rows:** {left_df._shape[0]} | **Right Rows:** {right_df._shape[0]}"
        )
        st.write(f"**Joined Rows:** {joined_df._shape[0]} (Inner Join)")
        st.write(f"**Joined Columns:** {joined_df._shape[1]}")

        # Display Data
        st.dataframe(joined_df.head(10).to_dict())

        # Column Inspector
        with st.expander("Inspect Joined Columns"):
            st.write(joined_df._columns)

    except Exception as e:
        st.error(f"An error occurred during join: {e}")
