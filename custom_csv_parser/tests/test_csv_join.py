"""
Unit test suite for pandas-like join syntax for DataFrame.
"""

import unittest
import os
from custom_csv_parser.csv_parser import CSVParser
from custom_csv_parser.dataframe import DataFrame

# How to run the tests:
# python -m unittest custom_csv_parser.tests.test_csv_join


class BaseDataFrameTest(unittest.TestCase):
    """
    Base test class with common setup for DataFrame tests.
    """

    # --- Test Setup ---
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.abspath(os.path.join(_current_dir, "..", ".."))
    DONOR_METADATA_FILE = os.path.join(
        _project_root,
        "data/sea-ad_cohort_donor_metadata_072524.csv",
    )
    MRI_FILE = os.path.join(
        _project_root,
        "data/sea-ad_cohort_mri_volumetrics.csv",
    )

    @classmethod
    def setUpClass(cls):
        """
        Set up test data before each test method by parsing the CSV file.
        """
        cls.donor_df = CSVParser(filepath=cls.DONOR_METADATA_FILE).parse()
        cls.mri_df = CSVParser(filepath=cls.MRI_FILE).parse()


class TestDataFrameJoin(BaseDataFrameTest):
    """
    Test suite for basic DataFrame join operations.
    """

    def test_inner_join(self):
        """Tests a standard inner join on 'Donor ID'."""

        # Perform the join
        joined_df = self.donor_df.join(
            self.mri_df, left_on="Donor ID", right_on="Donor ID"
        )

        self.assertIsInstance(joined_df, DataFrame)

        # Test shape: Number of rows should be the number of donors present in both files
        # It should be less than or equal to the left df row count
        self.assertLessEqual(joined_df._shape[0], self.donor_df._shape[0])
        self.assertGreater(joined_df._shape[0], 0)  # Should have some matches

        # Test shape: Number of columns should be (left_cols + right_cols - 1)
        expected_cols = (self.donor_df._shape[1] + self.mri_df._shape[1]) - 1
        self.assertEqual(joined_df._shape[1], expected_cols)

        # Test columns: Check that key columns and data columns are present
        self.assertIn("Donor ID", joined_df._columns)
        self.assertIn("Sex", joined_df._columns)  # From left df
        self.assertIn(
            "Left Thalamus Proper Volume", joined_df._columns
        )  # From right df

        # Check that the join key from the right table is not duplicated
        self.assertNotIn("Donor ID_right", joined_df._columns)
        self.assertNotIn("Donor ID_left", joined_df._columns)

    def test_join_with_column_collision(self):
        """Tests that join handles column name collisions with suffixes."""
        # Create dummy dataframes with a colliding column name "Notes"
        left_data = {"ID": ["A", "B", "C"], "Notes": ["L1", "L2", "L3"]}
        left_df = DataFrame(left_data, ["ID", "Notes"])

        right_data = {"ID": ["A", "B", "D"], "Notes": ["R1", "R2", "R4"]}
        right_df = DataFrame(right_data, ["ID", "Notes"])

        joined_df = left_df.join(right_df, left_on="ID", right_on="ID")

        # Check that columns are correctly renamed
        self.assertIn("Notes_left", joined_df._columns)
        self.assertIn("Notes_right", joined_df._columns)
        self.assertIn("ID", joined_df._columns)

        # Check data integrity
        joined_dict = joined_df.to_dict()
        self.assertEqual(joined_dict["Notes_left"], ["L1", "L2"])
        self.assertEqual(joined_dict["Notes_right"], ["R1", "R2"])


class TestDataFrameJoinErrorHandling(BaseDataFrameTest):
    """
    Test suite for join error handling and validation.
    """

    def test_join_invalid_join_type(self):
        """Tests that unsupported join types raise ValueError."""
        left_data = {"ID": ["A", "B"], "Value": [1, 2]}
        left_df = DataFrame(left_data, ["ID", "Value"])

        right_data = {"ID": ["A", "B"], "Name": ["X", "Y"]}
        right_df = DataFrame(right_data, ["ID", "Name"])

        # Attempt left join (not supported)
        with self.assertRaises(ValueError) as context:
            left_df.join(right_df, "ID", "ID", how="left")

        self.assertIn("not supported", str(context.exception))
        self.assertIn("inner", str(context.exception))

    def test_join_left_key_not_found(self):
        """Tests that joining on non-existent left column raises KeyError."""
        left_data = {"ID": ["A", "B"], "Value": [1, 2]}
        left_df = DataFrame(left_data, ["ID", "Value"])

        right_data = {"ID": ["A", "B"], "Name": ["X", "Y"]}
        right_df = DataFrame(right_data, ["ID", "Name"])

        with self.assertRaises(KeyError) as context:
            left_df.join(right_df, "NonExistentCol", "ID")

        self.assertIn("not found", str(context.exception))
        self.assertIn("left", str(context.exception))

    def test_join_right_key_not_found(self):
        """Tests that joining on non-existent right column raises KeyError."""
        left_data = {"ID": ["A", "B"], "Value": [1, 2]}
        left_df = DataFrame(left_data, ["ID", "Value"])

        right_data = {"ID": ["A", "B"], "Name": ["X", "Y"]}
        right_df = DataFrame(right_data, ["ID", "Name"])

        with self.assertRaises(KeyError) as context:
            left_df.join(right_df, "ID", "NonExistentCol")

        self.assertIn("not found", str(context.exception))
        self.assertIn("right", str(context.exception))

    def test_join_right_df_not_dataframe(self):
        """Tests that joining with non-DataFrame raises TypeError."""
        left_data = {"ID": ["A", "B"], "Value": [1, 2]}
        left_df = DataFrame(left_data, ["ID", "Value"])

        # Try to join with a list instead of DataFrame
        with self.assertRaises(TypeError) as context:
            left_df.join([1, 2, 3], "ID", "ID")

        self.assertIn("DataFrame", str(context.exception))

    def test_join_key_columns_not_strings(self):
        """Tests that join key parameters must be strings."""
        left_data = {"ID": ["A", "B"], "Value": [1, 2]}
        left_df = DataFrame(left_data, ["ID", "Value"])

        right_data = {"ID": ["A", "B"], "Name": ["X", "Y"]}
        right_df = DataFrame(right_data, ["ID", "Name"])

        # Try with integer key
        with self.assertRaises(TypeError) as context:
            left_df.join(right_df, 0, "ID")

        self.assertIn("string", str(context.exception))


class TestDataFrameJoinManyToMany(BaseDataFrameTest):
    """
    Test suite for many-to-many join scenarios.
    """

    def test_join_many_to_many(self):
        """Tests that join correctly handles true many-to-many relationships.

        When multiple left rows match multiple right rows, the result should have
        a Cartesian product of those matches.

        Example:
        - Left has ID=A twice, ID=B once
        - Right has ID=A once, ID=B twice
        - Result: 2 rows for A (2 left × 1 right) + 2 rows for B (1 left × 2 right) = 4 rows
        """
        # Left: 3 rows with duplicate ID A (many)
        left_data = {"ID": ["A", "A", "B"], "Value": [1, 2, 3]}
        left_df = DataFrame(left_data, ["ID", "Value"])

        # Right: 3 rows with duplicate ID B (many)
        right_data = {"ID": ["A", "B", "B"], "Name": ["X", "Y", "Z"]}
        right_df = DataFrame(right_data, ["ID", "Name"])

        joined_df = left_df.join(right_df, "ID", "ID")

        # Expected: 4 rows in result
        # ID=A: 2 left rows × 1 right row = 2 result rows
        # ID=B: 1 left row × 2 right rows = 2 result rows
        # Total: 4 rows
        self.assertEqual(joined_df._shape[0], 4)

        # Verify data integrity
        joined_dict = joined_df.to_dict()
        self.assertEqual(joined_dict["ID"], ["A", "A", "B", "B"])
        self.assertEqual(joined_dict["Value"], [1, 2, 3, 3])
        # Name should show Cartesian product: both A rows join with X, B row joins with Y and Z
        self.assertEqual(joined_dict["Name"], ["X", "X", "Y", "Z"])

    def test_join_one_to_many(self):
        """Tests that join correctly handles one-to-many relationships.

        When one left row matches multiple right rows, each match creates a result row.

        Example:
        - Left has ID=A once, ID=B once, ID=C once
        - Right has ID=A twice, ID=B once, ID=C missing
        - Result: 2 rows for A (1 left × 2 right) + 1 row for B (1 left × 1 right) = 3 rows
        """
        left_data = {"ID": ["A", "B", "C"], "Value": [1, 2, 3]}
        left_df = DataFrame(left_data, ["ID", "Value"])

        # Right has multiple rows for ID A (one-to-many from left perspective)
        right_data = {"ID": ["A", "A", "B"], "Score": [10, 20, 30]}
        right_df = DataFrame(right_data, ["ID", "Score"])

        joined_df = left_df.join(right_df, "ID", "ID")

        # A matches 2 rows, B matches 1 row, C has no match → 3 total
        self.assertEqual(joined_df._shape[0], 3)
        self.assertEqual(len(joined_df["ID"]), 3)

    def test_join_no_matches(self):
        """Tests that join with no matching keys returns empty DataFrame."""
        left_data = {"ID": ["A", "B"], "Value": [1, 2]}
        left_df = DataFrame(left_data, ["ID", "Value"])

        # Right has completely different IDs
        right_data = {"ID": ["X", "Y"], "Name": ["P", "Q"]}
        right_df = DataFrame(right_data, ["ID", "Name"])

        joined_df = left_df.join(right_df, "ID", "ID")

        # No matches → 0 rows
        self.assertEqual(joined_df._shape[0], 0)
        # But should have correct columns
        self.assertIn("ID", joined_df._columns)
        self.assertIn("Value", joined_df._columns)
        self.assertIn("Name", joined_df._columns)


class TestDataFrameJoinDifferentKeyNames(BaseDataFrameTest):
    """
    Test suite for joins where left and right use different key column names.
    """

    def test_join_different_key_column_names(self):
        """Tests join when left and right use different column names for the key."""
        left_data = {"PersonID": ["A", "B", "C"], "Value": [1, 2, 3]}
        left_df = DataFrame(left_data, ["PersonID", "Value"])

        right_data = {"DonorID": ["A", "B"], "Score": [100, 200]}
        right_df = DataFrame(right_data, ["DonorID", "Score"])

        joined_df = left_df.join(right_df, left_on="PersonID", right_on="DonorID")

        # A and B match, C doesn't → 2 rows
        self.assertEqual(joined_df._shape[0], 2)

        # Check columns
        self.assertIn("PersonID", joined_df._columns)
        self.assertIn("DonorID", joined_df._columns)
        self.assertIn("Value", joined_df._columns)
        self.assertIn("Score", joined_df._columns)

        # Verify data
        joined_dict = joined_df.to_dict()
        self.assertEqual(joined_dict["PersonID"], ["A", "B"])
        self.assertEqual(joined_dict["DonorID"], ["A", "B"])
        self.assertEqual(joined_dict["Value"], [1, 2])
        self.assertEqual(joined_dict["Score"], [100, 200])


class TestDataFrameJoinDataIntegrity(BaseDataFrameTest):
    """
    Test suite for data integrity and correctness after joins.
    """

    def test_join_preserves_data_types(self):
        """Tests that join preserves the original data from both DataFrames."""
        left_data = {"ID": ["A", "B"], "Age": ["30", "25"]}
        left_df = DataFrame(left_data, ["ID", "Age"])

        right_data = {"ID": ["A", "B"], "Score": ["95", "87"]}
        right_df = DataFrame(right_data, ["ID", "Score"])

        joined_df = left_df.join(right_df, "ID", "ID")

        # Data should be preserved as strings (CSV parser returns strings)
        joined_dict = joined_df.to_dict()
        self.assertEqual(joined_dict["Age"], ["30", "25"])
        self.assertEqual(joined_dict["Score"], ["95", "87"])

    def test_join_order_of_rows_matches_left(self):
        """Tests that result row order follows the left DataFrame order."""
        left_data = {"ID": ["B", "A", "C"], "Value": [2, 1, 3]}
        left_df = DataFrame(left_data, ["ID", "Value"])

        right_data = {"ID": ["A", "B", "C"], "Name": ["X", "Y", "Z"]}
        right_df = DataFrame(right_data, ["ID", "Name"])

        joined_df = left_df.join(right_df, "ID", "ID")

        # Order should follow left: B, A, C
        joined_dict = joined_df.to_dict()
        self.assertEqual(joined_dict["ID"], ["B", "A", "C"])
        self.assertEqual(joined_dict["Value"], [2, 1, 3])
        self.assertEqual(joined_dict["Name"], ["Y", "X", "Z"])

    def test_join_with_empty_left_dataframe(self):
        """Tests join when left DataFrame is empty."""
        left_data = {"ID": [], "Value": []}
        left_df = DataFrame(left_data, ["ID", "Value"])

        right_data = {"ID": ["A", "B"], "Name": ["X", "Y"]}
        right_df = DataFrame(right_data, ["ID", "Name"])

        joined_df = left_df.join(right_df, "ID", "ID")

        # Empty left → empty result
        self.assertEqual(joined_df._shape[0], 0)

    def test_join_with_empty_right_dataframe(self):
        """Tests join when right DataFrame is empty."""
        left_data = {"ID": ["A", "B"], "Value": [1, 2]}
        left_df = DataFrame(left_data, ["ID", "Value"])

        right_data = {"ID": [], "Name": []}
        right_df = DataFrame(right_data, ["ID", "Name"])

        joined_df = left_df.join(right_df, "ID", "ID")

        # Empty right → no matches → empty result
        self.assertEqual(joined_df._shape[0], 0)

    def test_join_chaining_with_filter(self):
        """Tests that joined DataFrames can be chained with filter operations."""
        left_data = {"ID": ["A", "B", "C"], "Age": ["30", "25", "35"]}
        left_df = DataFrame(left_data, ["ID", "Age"])

        right_data = {"ID": ["A", "B", "C"], "Active": ["Yes", "No", "Yes"]}
        right_df = DataFrame(right_data, ["ID", "Active"])

        joined_df = left_df.join(right_df, "ID", "ID")

        # Filter joined result for Active=Yes
        filtered = joined_df[joined_df["Active"] == "Yes"]

        # Should have A and C
        self.assertEqual(filtered._shape[0], 2)
        filtered_dict = filtered.to_dict()
        self.assertEqual(filtered_dict["ID"], ["A", "C"])


class TestDataFrameJoinRealData(BaseDataFrameTest):
    """
    Test suite for join operations on real CSV data.
    """

    def test_join_with_real_csv_data(self):
        """Tests join on actual project CSV data (donor metadata + MRI data)."""
        # Already tested in TestDataFrameJoin.test_inner_join
        # This is a consistency check
        joined_df = self.donor_df.join(
            self.mri_df, left_on="Donor ID", right_on="Donor ID"
        )

        self.assertIsInstance(joined_df, DataFrame)
        self.assertGreater(joined_df._shape[0], 0)
        self.assertGreater(joined_df._shape[1], 0)

    def test_join_preserves_all_left_rows_with_match(self):
        """Tests that all left rows with matches appear in the result."""
        joined_df = self.donor_df.join(
            self.mri_df, left_on="Donor ID", right_on="Donor ID"
        )

        # Get unique donor IDs from join result
        joined_ids = set(joined_df["Donor ID"])

        # Get donor IDs present in MRI data
        mri_ids = set(self.mri_df["Donor ID"])

        # All IDs in result should be in MRI data
        self.assertTrue(joined_ids.issubset(mri_ids))

    def test_join_result_can_be_aggregated(self):
        """Tests that joined DataFrame can be used with groupby/agg."""
        joined_df = self.donor_df.join(
            self.mri_df, left_on="Donor ID", right_on="Donor ID"
        )

        # Group by Sex and count
        if "Sex" in joined_df._columns:
            grouped = joined_df.groupby("Sex")
            result = grouped.agg({"Donor ID": "count"})

            # Should have groupby results
            self.assertGreater(result._shape[0], 0)
            self.assertEqual(result._columns[0], "Sex")
