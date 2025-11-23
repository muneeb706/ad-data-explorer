# SEA-AD Data Explorer

## 🧠 About the Tool

The **SEA-AD Data Explorer** is a web-based analytical tool designed to explore real-world data from the [Seattle Alzheimer's Disease (SEA-AD)](https://brain-map.org/consortia/sea-ad/our-data) research cohort.

This project was built by implementing a **custom SQL-style query engine from scratch** using pure Python. It **does not use Pandas** or any other data manipulation libraries. Instead, it relies on a custom-built `CSVParser` and `DataFrame` class to parse, filter, project, aggregate, and join datasets efficiently.

### 📂 The Dataset

The tool ships with the following datasets from the [SEA-AD cohort](https://brain-map.org/consortia/sea-ad/our-data):

- **Donor Metadata:** Demographics, age at death, and cognitive status.
- **Neuropathology:** Quantitative measurements of neuropathology (e.g., plaques, tangles).
- **Cognitive Scores:** Harmonized cognitive testing results.
- **MRI Volumetrics:** Brain scan volume measurements.

## 🛠 Functionalities & Features

The tool supports the following SQL-like operations:

- **Custom Parsing:** Reads CSV files, handling custom separators and quoted values.
- **Projection:** Selects specific columns from a dataset.
- **Filtering:** Filters rows based on conditional logic (supports `==`, `!=`, `>`, `<`, `>=`, `<=`).
- **Grouping & Aggregation:** Groups data by a categorical column and performs summary calculations (`count`, `mean`, `max`, `min`).
- **Joining:** Merges two datasets based on a common key (Inner Join).

## ⚙️ Internal Engine Implementation (No Pandas)

The core logic resides in the `custom_csv_parser` package. It is implemented entirely in standard Python to simulate how database engines handle data.

### 1. Custom Parser (`CSVParser`)

Located in `csv_parser.py`, this class reads raw text files line-by-line.

- **Logic:** It iterates through characters to handle complex CSV rules, such as values enclosed in quotes (e.g., `"New York, NY"`) which contain the delimiter.
- **Output:** Converts raw text into a custom `DataFrame` object.

### 2. Custom DataFrame (`DataFrame`)

Located in `dataframe.py`, this class mimics the behavior of a Pandas DataFrame using native Python data structures.

- **Data Structure:** Data is stored as a dictionary of lists (`{col_name: [value1, value2, ...]}`). This columnar storage allows for efficient retrieval of specific columns.

- **Projection (Column Selection):**

  - **Implementation:** Handled by the `__getitem__` method.
  - **Logic:** When a list of column names is passed (e.g., `df[['ID', 'Age']]`), the engine constructs a new dictionary containing _only_ the key-value pairs for those specific columns. It returns a new `DataFrame` object built from this subset, effectively slicing the data vertically without copying the entire dataset structure.

- **Filtering:**

  - **Implementation:** Uses boolean masking.
  - **Logic:** When a condition is applied (e.g., `df['Age'] > 80`), the engine generates a list of `True`/`False` values. The `filter` method then iterates through the data, keeping only the indices where the mask is `True`.

- **Grouping & Aggregation:**

  - **Grouping:** The `groupby` method partitions the data into a dictionary of smaller `DataFrame` objects, where each key is a unique value from the grouping column (e.g., 'Male', 'Female').
  - **Aggregation:** The `agg` method iterates through these groups. For each group, it extracts the target column's list of values and performs pure Python math operations (e.g., `sum(data) / len(data)` for mean, `max(data)` for max). It constructs a summary `DataFrame` from these calculated results.

- **Join Optimization:**
  - **Implementation:** The `join` method implements an **Inner Join** using a **Hash Index** approach for efficiency (O(N) complexity) rather than a nested loop (O(N\*M)).
  - **Logic:**
    1.  It builds a hash map (dictionary) of the _Right_ DataFrame's join keys.
    2.  It iterates through the _Left_ DataFrame once, performing O(1) lookups against the hash map to find matches.
    3.  It automatically handles column name collisions by appending `_left` and `_right` suffixes.

## 🖥️ User Interface (Streamlit)

The UI is built using **Streamlit** to provide an interactive wrapper around the custom engine.

### **1. Welcome (Home Page)**

- **File:** `Welcome.py`
- **Function:** Loads the four preset SEA-AD datasets. It demonstrates the engine's power by performing a massive **4-way Join**, merging Metadata, MRI, Neuropathology, and Cognitive scores into a single Master DataFrame based on `Donor ID`.

### **2. Filtering and Projection**

- **File:** `pages/1_Filtering_and_Projection.py`
- **Function:** Allows users to interactively clean data.
  - **Chain Operations:** Users can create a pipeline of operations (e.g., Filter Age > 90 -> Project 'Donor ID' -> Filter Sex == 'Male').
  - **Custom Uploads:** Supports uploading your own CSV files to test the parser.

### **3. Grouping and Aggregation**

- **File:** `pages/2_Grouping_and_Aggregation.py`
- **Function:** Performs "Split-Apply-Combine" workflows.
  - **Split:** User selects a column to group by (e.g., `Sex`).
  - **Apply:** User selects columns and functions (e.g., `mean` of `Brain Weight`).
  - **Combine:** Displays the resulting summary table.

### **4. Join Datasets**

- **File:** `pages/3_Join.py`
- **Function:** Provides a visual interface to merge two datasets.
  - Users select a Left and Right dataset (preset or uploaded).
  - The tool identifies common columns to suggest as keys.
  - Displays the resulting merged table and its shape.

## 📂 Repository Structure

```text
📦 ad-data-explorer
 ┣ 📂 custom_csv_parser          # The Custom "No-Pandas" Engine
 ┃ ┣ 📜 csv_parser.py            # Logic for reading/parsing CSV text
 ┃ ┣ 📜 dataframe.py             # Logic for Filtering, Grouping, Joining
 ┃ ┗ 📂 tests                    # Unit tests for the engine
 ┃   ┣ 📜 test_csv_parser.py
 ┃   ┣ 📜 test_csv_filter_and_projection.py
 ┃   ┣ 📜 test_csv_join.py
 ┃   ┗ 📜 test_groupby_and_aggregation.py
 ┣ 📂 data                       # SEA-AD Dataset Files
 ┃ ┣ 📜 sea-ad_cohort_donor_metadata_072524.csv
 ┃ ┣ 📜 sea-ad_cohort_mri_volumetrics.csv
 ┃ ┣ 📜 sea-ad_all_mtg_quant_neuropath_bydonorid_081122.csv
 ┃ ┗ 📜 sea-ad_cohort_harmonized_cognitive_scores_20241213.csv
 ┣ 📂 pages                      # Streamlit UI Pages
 ┃ ┣ 📜 1_Filtering_and_Projection.py
 ┃ ┣ 📜 2_Grouping_and_Aggregation.py
 ┃ ┗ 📜 3_Join.py
 ┣ 📜 Welcome.py                 # Main Streamlit Application Entry Point
 ┣ 📜 requirements.txt           # Python dependencies
 ┗ 📜 README.md                  # Project Documentation
```

## Setup and Usage

### 1. Clone the Repository

Start by cloning the project to your local machine:

### 2. Prerequisites

Ensure you have Python installed (this applications was built and tested on Python 3.11.7 environment). It is recommended to use a virtual environment.

### 3. Installation

Install the required libraries

```bash
pip install -r requirements.txt
```

### 4. Running the Tests

Run the unit tests to ensure everything is working correctly:

```bash
pytest custom_csv_parser/tests
```

OR

```bash
python -m unittest discover -s custom_csv_parser/tests
```

### 5. Running the Application

Launch the web interface using Streamlit:

```bash
streamlit run Welcome.py
```

The application will open automatically in your default web browser at http://localhost:8501.
