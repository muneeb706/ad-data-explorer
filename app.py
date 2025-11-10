import streamlit as st
from custom_csv_parser.csv_parser import CSVParser
from custom_csv_parser.dataframe import DataFrame
import os
import time

# --- 1. Page Configuration ---
st.set_page_config(page_title="SEA-AD Data Explorer", page_icon="🧠", layout="wide")

# --- 2. File Paths ---
DATA_DIR = "data"
DONOR_METADATA_FILE = os.path.join(DATA_DIR, "sea-ad_cohort_donor_metadata_072524.csv")
MRI_FILE = os.path.join(DATA_DIR, "sea-ad_cohort_mri_volumetrics.csv")
NEUROPATH_FILE = os.path.join(
    DATA_DIR, "sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv"
)
COGNITIVE_FILE = os.path.join(
    DATA_DIR, "sea-ad_cohort_harmonized_cognitive_scores_20241213.csv"
)


# --- 3. Master Data Loading Function ---
# It uses @st.cache_data to run only once
@st.cache_data
def load_data():
    """
    Parses all CSVs and joins them into a single master DataFrame.
    This demonstrates all required functions from the project guideline:
    1. CSVParser (from custom_csv_parser.csv_parser)
    2. DataFrame.join (from custom_csv_parser.dataframe)
    """
    try:
        start_time = time.time()
        # 1. PARSE
        donor_df = CSVParser(filepath=DONOR_METADATA_FILE).parse()
        mri_df = CSVParser(filepath=MRI_FILE).parse()
        neuropath_df = CSVParser(filepath=NEUROPATH_FILE).parse()
        cognitive_df = CSVParser(filepath=COGNITIVE_FILE).parse()

        # 2. JOIN
        # Join all four datasets into one master table
        master_df = donor_df.join(mri_df, left_on="Donor ID", right_on="Donor ID")
        master_df = master_df.join(
            neuropath_df, left_on="Donor ID", right_on="Donor ID"
        )
        master_df = master_df.join(
            cognitive_df, left_on="Donor ID", right_on="Donor ID"
        )

        end_time = time.time()
        load_time = end_time - start_time

        return master_df, load_time
    except FileNotFoundError as e:
        st.error(
            f"Error loading data file: {e}. Make sure the 'data' directory is correct."
        )
        return None, 0
    except Exception as e:
        st.error(f"An error occurred during data loading and joining: {e}")
        return None, 0


# --- 4. Main App Logic ---
st.title("🧠 Welcome to the SEA-AD Data Explorer")
st.subheader(
    "A data exploration tool that uses a custom Python library (built from scratch, without pandas) to parse, join, filter, group, and analyze data."
)

st.markdown(
    """
**This application demonstrates all required functions:**
* **Parsing:** All data is loaded from the CSV files using the `CSVParser`.
* **Join:** The four datasets are merged into one master table using the `join()` method.
* **Filtering, Projection, Group By, Aggregation:** These functions are used in the 'Data Explorer' and 'Comparative Analysis' pages.

Use the sidebar to navigate to the different tools.
"""
)

# --- 5. Load Data and Store in Session ---
# Check if data is already loaded to avoid re-running
if "master_df" not in st.session_state:
    with st.spinner("Loading and joining datasets... This may take a moment."):
        master_df, load_time = load_data()

        if master_df:
            # Store the loaded data in the session state
            st.session_state["master_df"] = master_df
            st.success(
                f"Successfully loaded and joined datasets in {load_time:.2f} seconds."
            )
            st.info(f"Master DataFrame created with shape: {master_df._shape}")
            st.dataframe(master_df.head(5).to_dict())
        else:
            st.error("Failed to load data. The application cannot proceed.")
else:
    st.success("Master dataset is already loaded.")
    st.info(f"Master DataFrame shape: {st.session_state['master_df']._shape}")

st.sidebar.success("Select an analysis page to begin.")
