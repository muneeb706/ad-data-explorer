import unittest
import os

# (custom_csv_parser) to find the 'parsers' and 'dataframe' modules.
from custom_csv_parser.csv_parser import CSVParser
from custom_csv_parser.dataframe import DataFrame

# How to run the tests:
# python -m unittest custom_csv_parser.tests.test_csv_parser


class TestCSVParser(unittest.TestCase):
    """
    Test suite for the CSVParser class.
    """

    # --- Test Setup ---
    # Get the absolute path to the directory of the current test script
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct paths to the project's root directory (which is two levels up)
    _project_root = os.path.abspath(os.path.join(_current_dir, "..", ".."))

    DONOR_METADATA_FILE = os.path.join(
        _project_root,
        "data/sea-ad_cohort_donor_metadata_072524.csv",
    )
    NON_EXISTENT_FILE = os.path.join(_project_root, "data/no_file_here.csv")

    def test_successful_parsing(self):
        """
        Tests that a valid CSV file is parsed correctly into a DataFrame.
        """

        parser = CSVParser(filepath=self.DONOR_METADATA_FILE)
        df = parser.parse()

        self.assertIsInstance(
            df, DataFrame, "Parse method should return a DataFrame object."
        )
        self.assertGreater(df._shape[0], 0, "DataFrame should have rows.")
        # last column is empty column
        self.assertEqual(df._shape[1], 67, "DataFrame should have 67 columns.")
        self.assertIn("Donor ID", df._columns)
        self.assertIn("Age at Death", df._columns)
        self.assertIn("Sex", df._columns)
        self.assertIn("If other Consensus dx, describe", df._columns)

        # find this value in the dataframe, MCI multidomain (amnestic, language, attention, executive, visuospatial)
        self.assertEqual(
            "MCI multidomain (amnestic, language, attention, executive, visuospatial)",
            df._data["If other Consensus dx, describe"][28],
        )

    def test_file_not_found_error(self):
        """
        Tests that the parser raises FileNotFoundError for a non-existent file.
        """
        parser = CSVParser(filepath=self.NON_EXISTENT_FILE)
        with self.assertRaises(FileNotFoundError):
            parser.parse()

    def test_head_function(self):
        """
        Tests the DataFrame.head() method returns the correct number of rows.
        """
        parser = CSVParser(filepath=self.DONOR_METADATA_FILE)
        df = parser.parse()

        # Test default head (5 rows)
        head_df = df.head()
        self.assertIsInstance(
            head_df, DataFrame, "head() should return a DataFrame object."
        )
        self.assertEqual(
            head_df._shape[0], 5, "head() should return 5 rows by default."
        )
        self.assertEqual(
            head_df._shape[1],
            df._shape[1],
            "head() should have same number of columns as original.",
        )

        # Test custom n value (10 rows)
        head_df_10 = df.head(10)
        self.assertEqual(head_df_10._shape[0], 10, "head(10) should return 10 rows.")
        self.assertEqual(
            head_df_10._shape[1],
            df._shape[1],
            "head(10) should have same number of columns as original.",
        )

        # Test head with n larger than DataFrame size
        total_rows = df._shape[0]
        head_df_large = df.head(total_rows + 100)
        self.assertEqual(
            head_df_large._shape[0],
            total_rows,
            "head(n) where n > total rows should return all rows.",
        )

        # Verify the data integrity (first row values match)
        first_donor_id = df._data["Donor ID"][0]
        head_first_donor_id = head_df._data["Donor ID"][0]
        self.assertEqual(
            first_donor_id,
            head_first_donor_id,
            "First row data should match between original and head().",
        )

    def test_generic_exception_handling(self):
        """
        Tests that generic exceptions are caught and re-raised during parsing.
        This test simulates an error by providing invalid input.
        """
        import tempfile

        # Create a temporary file with inconsistent column counts
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as temp_file:
            temp_file.write("Col1,Col2,Col3\n")
            temp_file.write("val1,val2,val3\n")
            temp_file.write("val4,val5\n")  # This row has only 2 values instead of 3
            temp_file_path = temp_file.name

        try:
            parser = CSVParser(filepath=temp_file_path)
            with self.assertRaises(ValueError) as context:
                parser.parse()

            # Verify the error message mentions the row and column count mismatch
            self.assertIn("Expected 3 columns", str(context.exception))
            self.assertIn("but found 2", str(context.exception))

        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)

    def test_empty_file_handling(self):
        """
        Tests that parsing an empty file returns an empty DataFrame.
        """
        import tempfile

        # Create an empty temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as temp_file:
            temp_file_path = temp_file.name

        try:
            parser = CSVParser(filepath=temp_file_path)
            df = parser.parse()

            self.assertIsInstance(df, DataFrame, "Should return a DataFrame object.")
            self.assertEqual(
                df._shape[0], 0, "Empty file should return DataFrame with 0 rows."
            )
            self.assertEqual(
                df._shape[1], 0, "Empty file should return DataFrame with 0 columns."
            )

        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)

    def test_skip_empty_lines_at_end(self):
        """
        Tests that empty lines at the end of the file are properly skipped.
        """
        import tempfile

        # Create a temporary file with multiple empty lines at the end
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv"
        ) as temp_file:
            temp_file.write("Name,Age\n")
            temp_file.write("Alice,25\n")
            temp_file.write("Bob,30\n")
            temp_file.write("\n")
            temp_file.write("\n")
            temp_file.write("\n")
            temp_file_path = temp_file.name

        try:
            parser = CSVParser(filepath=temp_file_path)
            df = parser.parse()

            self.assertIsInstance(df, DataFrame, "Should return a DataFrame object.")
            self.assertEqual(df._shape[0], 2, "Should have 2 data rows.")
            self.assertEqual(df._data["Name"], ["Alice", "Bob"])
            self.assertEqual(df._data["Age"], ["25", "30"])

        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
