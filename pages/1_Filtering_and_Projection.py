import streamlit as st
from custom_csv_parser.dataframe import DataFrame
from custom_csv_parser.csv_parser import CSVParser  # Import the parser
import time
import os

# --- Page Config ---
st.set_page_config(page_title="Filtering and Projection", page_icon="🛠️", layout="wide")

st.title("🛠️ Filtering and Projection")
st.markdown(
    """
This page lets you interactively test the **Filtering** and **Projection** capabilities on the **individual** datasets.
"""
)

# --- File Paths ---
DATA_DIR = "data"
# Citing the data files from the repository
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


# --- Helper Function to apply comparison ---
def apply_comparison(df, column, op, value):
    """
    Applies the correct comparison operator to the DataFrame.
    This uses the Series's overloaded operators.
    """
    series = df[column]

    # Try to convert value to a number for numeric comparisons
    # try:
    #     numeric_value = float(value)
    #     value = numeric_value
    # except (ValueError, TypeError):
    #     # Keep as string if it's not a number (e.g., 'Female')
    #     pass

    print(f"Applying comparison: {column} {op} {value}")
    print(f"Series sample data: {series[:5]}")
    # Citing the Series comparison operators
    if op == "==":
        mask = series == value
    elif op == "!=":
        mask = series != value
    elif op == ">":
        mask = series > value
    elif op == "<":
        mask = series < value
    elif op == ">=":
        mask = series >= value
    elif op == "<=":
        mask = series <= value
    else:
        raise ValueError("Invalid operator")

    return df[mask]


# --- 1. Setup: Select Dataset ---
st.header("Step 1: Select a Dataset to Operate On")

selected_df_name = st.selectbox("Choose a dataset:", AVAILABLE_FILES.keys())


# --- 2. Load Data On-Demand ---
# This is the new logic to load only the selected file.
@st.cache_data(show_spinner=f"Parsing {selected_df_name}...")
def load_selected_df(file_path):
    """
    Parses the selected CSV file using the custom CSVParser.
    """
    try:
        return CSVParser(filepath=file_path).parse()
    except Exception as e:
        st.error(f"Error parsing {file_path}: {e}")
        return None


file_path = AVAILABLE_FILES[selected_df_name]
df = load_selected_df(file_path)

if df is None:
    st.error("Data loading failed. Please check file paths and permissions.")
    st.stop()

st.info(
    f"Selected **{selected_df_name}** with shape: {df._shape[0]} rows × {df._shape[1]} columns."
)
# Citing head() and to_dict() methods
st.dataframe(df.to_dict())


# --- 3. Select Operation ---
st.header("Step 2: Choose and Configure an Operation")

operation = st.selectbox("Select operation:", ["Filtering", "Projection"])

if operation == "Projection":
    st.subheader("Configure Projection")

    all_columns = df._columns
    selected_columns = st.multiselect(
        "Select columns to project:",
        options=all_columns,
        default=list(all_columns[:3]),  # Default to first 3 columns
    )

    if st.button("Run Projection"):
        if not selected_columns:
            st.warning("Please select at least one column.")
        else:
            try:
                # --- PROJECTION LOGIC ---
                with st.spinner("Applying projection..."):
                    start_time = time.time()
                    result_df = df[selected_columns]
                    end_time = time.time()

                st.session_state["last_result_df"] = result_df  # Save to memory

                st.success(
                    f"Projection complete in {end_time - start_time:.4f} seconds."
                )
                st.info(
                    f"Resulting DataFrame shape: {result_df._shape[0]} rows × {result_df._shape[1]} columns."
                )
                st.dataframe(result_df.to_dict())

            except Exception as e:
                st.error(f"An error occurred: {e}")

elif operation == "Filtering":
    st.subheader("Configure Filter")

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_column = st.selectbox("Column:", df._columns)
    with col2:
        operator = st.selectbox("Operator:", ["==", "!=", ">", "<", ">=", "<="])
    with col3:
        value = st.text_input(
            "Value:",
            help="Enter the value to compare against (e.g., 'Female', '80')",
        )

    if st.button("Run Comparison Filter"):
        if not value:
            st.warning("Please enter a value.")
        else:
            try:
                # --- FILTERING LOGIC (COMPARISON) ---
                with st.spinner("Applying filter..."):
                    start_time = time.time()
                    result_df = apply_comparison(df, selected_column, operator, value)
                    end_time = time.time()

                st.session_state["last_result_df"] = result_df  # Save to memory

                st.success(f"Filter complete in {end_time - start_time:.4f} seconds.")
                st.info(
                    f"Found **{result_df._shape[0]}** matching rows. Shape: {result_df._shape[0]} rows × {result_df._shape[1]} columns."
                )
                st.dataframe(result_df.to_dict())

            except Exception as e:
                st.error(
                    f"An error occurred. This is often due to comparing incompatible types (e.g., '>' on a string). Error: {e}"
                )

# --- 4. Display Last Result ---
st.header("Last Operation Result")
if st.session_state.get("last_result_df") is not None:
    st.markdown(
        "This is the DataFrame currently saved in memory from your last operation."
    )
    last_shape = st.session_state["last_result_df"]._shape
    st.info(f"Shape: {last_shape[0]} rows × {last_shape[1]} columns.")
    st.dataframe(st.session_state["last_result_df"].to_dict())
else:
    st.markdown("No operation has been performed yet.")
