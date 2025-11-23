import streamlit as st
from custom_csv_parser.csv_parser import CSVParser
import os

st.set_page_config(page_title="SEA-AD Data Explorer", page_icon="🧠", layout="wide")

# ---  Data File Paths ---
DATA_DIR = "data"
DONOR_METADATA_FILE = os.path.join(DATA_DIR, "sea-ad_cohort_donor_metadata_072524.csv")
MRI_FILE = os.path.join(DATA_DIR, "sea-ad_cohort_mri_volumetrics.csv")
NEUROPATH_FILE = os.path.join(
    DATA_DIR, "sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv"
)
COGNITIVE_FILE = os.path.join(
    DATA_DIR, "sea-ad_cohort_harmonized_cognitive_scores_20241213.csv"
)


# --- Master Data Loading Function ---
# It uses @st.cache_data to run only once
@st.cache_data
def load_individual_datasets():
    """
    Parses all four CSVs using the custom CSVParser.
    This demonstrates the PARSE function of the library.
    """
    try:
        # PARSE (Using your custom parser from csv_parser.py)
        donor_df = CSVParser(filepath=DONOR_METADATA_FILE).parse()
        mri_df = CSVParser(filepath=MRI_FILE).parse()
        neuropath_df = CSVParser(filepath=NEUROPATH_FILE).parse()
        cognitive_df = CSVParser(filepath=COGNITIVE_FILE).parse()

        return donor_df, mri_df, neuropath_df, cognitive_df

    except FileNotFoundError as e:
        st.error(
            f"Error loading data file: {e}. Make sure the 'data' directory is correct."
        )
        return None, None, None, None, 0
    except Exception as e:
        st.error(f"An error occurred during data loading: {e}")
        return None, None, None, None, 0


# --- Main App Logic ---
st.title("🧠 Welcome to the SEA-AD Data Explorer")
st.subheader(
    "A data exploration tool that uses a custom Python library (built from scratch, without pandas) to parse, join, filter, group, and aggregate [SEA-AD data](https://brain-map.org/consortia/sea-ad/our-data) for analysis. "
    "This tool also allows uploading custom CSV files to explore your own data."
)

st.markdown(
    """
**This application demonstrates use of following operations:**
* **Parsing:** Load data from the CSV files.
* **Filtering & Projection:** Select rows and columns.
* **Grouping & Aggregation:** Summarize data by groups.
* **Join:** Join / Merge data in CSV files.
"""
)

# --- Load, Explain, and Join Data ---
with st.spinner("Loading individual datasets using custom parser..."):
    donor_df, mri_df, neuropath_df, cognitive_df = load_individual_datasets()

    if donor_df:
        st.success("Successfully parsed all datasets.")

        # --- Explain and Show Individual Datasets ---
        st.header("Data Exploration: Individual Preset Datasets")
        st.markdown("First 3 rows and the shape of each preset dataset file:")

        st.subheader("1. Donor Metadata")
        st.markdown(
            "It contains the primary demographic and clinical information for each donor, like their `Donor ID`, `Sex`, `Age at Death`, and `Cognitive Status`."
        )
        st.dataframe(donor_df.head(3).to_dict())
        st.info(f"**Shape:** {donor_df._shape[0]} rows, {donor_df._shape[1]} columns")

        st.subheader("2. Cognitive Scores")
        st.markdown(
            "Contains harmonized cognitive test scores for the donors identified by `Donor ID`."
        )
        st.dataframe(cognitive_df.head(3).to_dict())
        st.info(
            f"**Shape:** {cognitive_df._shape[0]} rows, {cognitive_df._shape[1]} columns"
        )

        st.subheader("3. MRI Volumetrics")
        st.markdown(
            "Contains brain scan (MRI) measurements, such as the volume of the hippocampus, for donors identified by `Donor ID`."
        )
        st.dataframe(mri_df.head(3).to_dict())
        st.info(f"**Shape:** {mri_df._shape[0]} rows, {mri_df._shape[1]} columns")

        st.subheader("4. Neuropathology")
        st.markdown(
            "Contains detailed post-mortem data, like plaque measurements, for donors identified by `Donor ID`."
        )
        st.dataframe(neuropath_df.head(3).to_dict())
        st.info(
            f"**Shape:** {neuropath_df._shape[0]} rows, {neuropath_df._shape[1]} columns"
        )

        # --- Explain and Perform Join ---
        st.header("Data Exploration: Joining All Datasets")
        st.markdown(
            """
        Using `join()` function to combine all datasets into one 'master' dataset.
       Joining them all using a single common column: **`Donor ID`**.
        Here are the first 5 rows of the final joined data:
        """
        )

        with st.spinner("Joining datasets using `join()` method..."):
            master_df = donor_df.join(mri_df, left_on="Donor ID", right_on="Donor ID")
            master_df = master_df.join(
                neuropath_df, left_on="Donor ID", right_on="Donor ID"
            )
            master_df = master_df.join(
                cognitive_df, left_on="Donor ID", right_on="Donor ID"
            )

        st.success("Successfully joined all datasets!")
        st.dataframe(master_df.head(5).to_dict())
        st.info(
            f"**Master DataFrame Shape:** {master_df._shape[0]} rows, {master_df._shape[1]} columns"
        )
    else:
        st.error("Failed to load data. The application cannot proceed.")
