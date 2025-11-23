import streamlit as st
from custom_csv_parser.dataframe import DataFrame
from custom_csv_parser.csv_parser import CSVParser
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


# --- Robust Comparison Logic ---
def get_comparison_mask(df, column, op, value):
    """
    Generates a boolean mask for filtering, handling mixed types safely.
    It attempts numeric conversion per row to avoid crashes.
    """
    series = df[column]
    data = series._data  # Access raw data list

    # 1. Determine target value type
    try:
        target_val = float(value)
        is_numeric_target = True
    except (ValueError, TypeError):
        target_val = value
        is_numeric_target = False

    mask = []

    # 2. Iterate row by row (safer than bulk conversion)
    for x in data:
        row_val = x

        # If target is number, try to treat row value as number
        if is_numeric_target:
            try:
                if x is None or x == "":
                    row_val = None
                else:
                    row_val = float(x)
            except (ValueError, TypeError):
                # If conversion fails, treat as None (skip this row for inequality)
                row_val = None

        # 3. Perform Comparison
        if row_val is None:
            # None typically fails inequalities, safe to say False
            res = False
        else:
            try:
                if op == "==":
                    res = row_val == target_val
                elif op == "!=":
                    res = row_val != target_val
                elif op == ">":
                    res = row_val > target_val
                elif op == "<":
                    res = row_val < target_val
                elif op == ">=":
                    res = row_val >= target_val
                elif op == "<=":
                    res = row_val <= target_val
                else:
                    res = False
            except TypeError:
                # Fallback if types are still incompatible
                res = False

        mask.append(res)

    return mask


def apply_comparison_df(df, column, op, value):
    """Returns a filtered DataFrame using the robust mask logic."""
    mask = get_comparison_mask(df, column, op, value)
    return df[mask]


# --- 1. Setup: Select Dataset ---
st.header("Step 1: Select a Dataset to Operate On")

selected_df_name = st.selectbox("Choose a dataset:", AVAILABLE_FILES.keys())


# --- 2. Load Data On-Demand ---
@st.cache_data(show_spinner=f"Parsing {selected_df_name}...")
def load_selected_df(file_path):
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
st.dataframe(df.to_dict())


# --- 3. Select Operation ---
st.header("Step 2: Choose and Configure an Operation")

if "operations_chain" not in st.session_state:
    st.session_state.operations_chain = []

# Display applied operations chain
if st.session_state.operations_chain:
    st.markdown("**Applied Operations Chain:**")
    for idx, op_info in enumerate(st.session_state.operations_chain):
        col1, col2 = st.columns([4, 1])
        with col1:
            if op_info["type"] == "filter":
                st.text(f"  {idx + 1}. Filter: {op_info['description']}")
            else:
                st.text(f"  {idx + 1}. Projection: {', '.join(op_info['columns'])}")
        with col2:
            if st.button("🗑️", key=f"remove_op_{idx}"):
                st.session_state.operations_chain.pop(idx)
                st.rerun()
    st.divider()

operation = st.selectbox("Select operation to add:", ["Filtering", "Projection"])

if operation == "Projection":
    st.subheader("Configure Projection")

    if st.session_state.operations_chain:
        working_df = st.session_state.get("operations_result_df", df)
    else:
        working_df = df

    all_columns = working_df._columns
    selected_columns = st.multiselect(
        "Select columns to project:",
        options=all_columns,
        default=list(all_columns[:3]) if all_columns else None,
    )

    if st.button("Add Projection to Chain"):
        if not selected_columns:
            st.warning("Please select at least one column.")
        else:
            st.session_state.operations_chain.append(
                {"type": "projection", "columns": selected_columns}
            )
            st.rerun()

elif operation == "Filtering":
    st.subheader("Configure Filter(s)")

    if "filters" not in st.session_state:
        st.session_state.filters = []
    if "filter_logics" not in st.session_state:
        st.session_state.filter_logics = []

    # Display existing filters
    if st.session_state.filters:
        st.markdown("**Applied Filters:**")
        for idx, (col, op, val) in enumerate(st.session_state.filters):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                if idx == 0:
                    st.text(f"  • {col} {op} '{val}'")
                else:
                    logic_op = (
                        st.session_state.filter_logics[idx - 1]
                        if idx - 1 < len(st.session_state.filter_logics)
                        else "AND"
                    )
                    st.text(f"  {logic_op} {col} {op} '{val}'")
            with col2:
                if st.button("❌", key=f"remove_filter_{idx}"):
                    st.session_state.filters.pop(idx)
                    if idx < len(st.session_state.filter_logics):
                        st.session_state.filter_logics.pop(idx)
                    st.rerun()
        st.divider()

    st.markdown("**Add New Filter:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_column = st.selectbox("Column:", df._columns, key="new_filter_col")
    with col2:
        new_operator = st.selectbox(
            "Operator:", ["==", "!=", ">", "<", ">=", "<="], key="new_filter_op"
        )
    with col3:
        new_value = st.text_input(
            "Value:",
            help="Enter the value to compare against (e.g., 'Female', '80')",
            key="new_filter_value",
        )

    if st.button("Add Filter", use_container_width=True):
        if not new_value:
            st.warning("Please enter a value.")
        else:
            st.session_state.filters.append((new_column, new_operator, new_value))
            if len(st.session_state.filters) > 1:
                logic = st.session_state.get("pending_logic", "AND")
                st.session_state.filter_logics.append(logic)
            st.rerun()

    if st.session_state.filters:
        if st.button("Add Filters to Chain", use_container_width=True):
            try:
                filter_desc = []
                for idx, (col, op, val) in enumerate(st.session_state.filters):
                    if idx == 0:
                        filter_desc.append(f"{col} {op} '{val}'")
                    else:
                        logic_op = (
                            st.session_state.filter_logics[idx - 1]
                            if idx - 1 < len(st.session_state.filter_logics)
                            else "AND"
                        )
                        filter_desc.append(f"{logic_op} {col} {op} '{val}'")

                st.session_state.operations_chain.append(
                    {
                        "type": "filter",
                        "filters": st.session_state.filters.copy(),
                        "filter_logics": st.session_state.filter_logics.copy(),
                        "description": " ".join(filter_desc),
                    }
                )

                st.session_state.filters = []
                st.session_state.filter_logics = []

                st.rerun()
            except Exception as e:
                st.error(f"Error adding filters to chain: {e}")

# --- 4. Execute Operations Chain ---
if st.session_state.operations_chain:
    if st.button("Execute Chain", use_container_width=True, type="primary"):
        try:
            with st.spinner("Executing operations chain..."):
                start_time = time.time()
                current_df = df

                for op in st.session_state.operations_chain:
                    if op["type"] == "filter":
                        masks = []
                        for col, op_type, val in op["filters"]:
                            # Use robust mask generation directly
                            mask = get_comparison_mask(current_df, col, op_type, val)
                            masks.append(mask)

                        if len(masks) == 1:
                            combined_mask = masks[0]
                        else:
                            combined_mask = masks[0]
                            for idx in range(1, len(masks)):
                                logic_op = (
                                    op["filter_logics"][idx - 1]
                                    if idx - 1 < len(op["filter_logics"])
                                    else "AND"
                                )
                                if logic_op == "AND":
                                    combined_mask = [
                                        combined_mask[i] and masks[idx][i]
                                        for i in range(current_df._shape[0])
                                    ]
                                else:
                                    combined_mask = [
                                        combined_mask[i] or masks[idx][i]
                                        for i in range(current_df._shape[0])
                                    ]
                        current_df = current_df[combined_mask]

                    elif op["type"] == "projection":
                        current_df = current_df[op["columns"]]

                end_time = time.time()

            st.session_state["last_result_df"] = current_df
            st.success(f"Chain executed in {end_time - start_time:.4f} seconds.")
            st.info(
                f"Final result shape: {current_df._shape[0]} rows × {current_df._shape[1]} columns."
            )
            st.dataframe(current_df.to_dict())

        except Exception as e:
            st.error(f"Error executing chain: {e}")

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
