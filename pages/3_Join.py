import streamlit as st
from custom_csv_parser.csv_parser import CSVParser
import os

# --- Page Config ---
st.set_page_config(page_title="Join Datasets", page_icon="🔗", layout="wide")

st.title("🔗 Join Datasets")
st.markdown(
    """
This page lets you interactively test the **Joining** capabilities on the selected datasets.
You can combine two datasets horizontally based on a common key column.
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


@st.cache_data(show_spinner=False)
def load_data(path):
    try:
        return CSVParser(filepath=path).parse()
    except Exception as e:
        return None


# --- Helper to select/upload file ---
def render_file_selector(key_prefix, label):
    st.subheader(label)
    source = st.radio(
        "Source:", ["Preset", "Upload"], key=f"{key_prefix}_source", horizontal=True
    )

    f_path = None
    if source == "Preset":
        name = st.selectbox(
            f"Choose {label}:", list(AVAILABLE_FILES.keys()), key=f"{key_prefix}_preset"
        )
        f_path = AVAILABLE_FILES[name]
    else:
        uploaded = st.file_uploader(
            f"Upload {label} CSV", type="csv", key=f"{key_prefix}_upload"
        )
        if uploaded:
            f_path = os.path.join(TMP_DIR, uploaded.name)
            with open(f_path, "wb") as f:
                f.write(uploaded.getbuffer())

    return f_path


# --- Select Datasets ---
st.header("Step 1: Select Datasets")

col1, col2 = st.columns(2)

left_df = None
right_df = None

with col1:
    left_path = render_file_selector("left", "Left Dataset")
    if left_path:
        left_df = load_data(left_path)
        if left_df:
            st.info(f"Loaded: {left_df._shape[0]} rows, {left_df._shape[1]} cols")
            with st.expander("View Data"):
                st.dataframe(left_df.head(3).to_dict())
        else:
            st.error("Error parsing file.")

with col2:
    right_path = render_file_selector("right", "Right Dataset")
    if right_path:
        right_df = load_data(right_path)
        if right_df:
            st.info(f"Loaded: {right_df._shape[0]} rows, {right_df._shape[1]} cols")
            with st.expander("View Data"):
                st.dataframe(right_df.head(3).to_dict())
        else:
            st.error("Error parsing file.")

# --- 2. Configure Join Keys ---
if left_df and right_df:
    st.header("Step 2: Configure Join Keys")

    # Find common columns to suggest as default
    common_cols = list(set(left_df._columns) & set(right_df._columns))

    c1, c2 = st.columns(2)
    with c1:
        # Default to "Donor ID" if present, otherwise first common col, otherwise first col
        l_idx = 0
        if "Donor ID" in left_df._columns:
            l_idx = left_df._columns.index("Donor ID")

        left_on = st.selectbox("Left Key Column:", left_df._columns, index=l_idx)

    with c2:
        r_idx = 0
        if "Donor ID" in right_df._columns:
            r_idx = right_df._columns.index("Donor ID")

        right_on = st.selectbox("Right Key Column:", right_df._columns, index=r_idx)

    # --- 3. Execute Join ---
    st.header("Step 3: Result")

    st.warning(
        "⚠️ **Note:** This engine supports only **Inner Join**. "
        "Non-matching rows will be excluded."
    )

    if st.button("Execute Inner Join", type="primary"):
        try:
            with st.spinner("Joining datasets..."):
                joined_df = left_df.join(right_df, left_on=left_on, right_on=right_on)

            st.success("Join successful!")

            st.write(
                f"**Left:** {left_df._shape[0]} rows | **Right:** {right_df._shape[0]} rows"
            )
            st.write(
                f"**Result:** {joined_df._shape[0]} rows, {joined_df._shape[1]} columns"
            )

            st.dataframe(joined_df.head(10).to_dict())

        except Exception as e:
            st.error(f"An error occurred during join: {e}")

else:
    st.info("Please select both datasets to proceed.")
