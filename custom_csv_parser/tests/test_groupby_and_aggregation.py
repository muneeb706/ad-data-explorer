"""
Unit test suite for DataFrame groupby and aggregation operations.
"""

import unittest
import os
from custom_csv_parser.csv_parser import CSVParser
from custom_csv_parser.dataframe import DataFrame, DataFrameGroupBy

# How to run the tests:
# python -m unittest custom_csv_parser.tests.test_groupby_and_aggregation


class BaseGroupByTest(unittest.TestCase):
    """
    Base test class with common setup for GroupBy tests.
    """

    # --- Test Setup ---
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _project_root = os.path.abspath(os.path.join(_current_dir, "..", ".."))
    DONOR_METADATA_FILE = os.path.join(
        _project_root,
        "data/sea-ad_cohort_donor_metadata_072524.csv",
    )

    def setUp(self):
        """
        Set up test data before each test method by parsing the CSV file.
        """
        parser = CSVParser(filepath=self.DONOR_METADATA_FILE)
        self.df = parser.parse()


class TestDataFrameGroupByAndAggregation(BaseGroupByTest):
    """
    Test suite for basic DataFrame groupby and aggregation operations.
    """

    def test_groupby_key_error(self):
        """Tests that grouping by a non-existent column raises a KeyError."""
        with self.assertRaises(KeyError):
            self.df.groupby("NonExistentColumn")

    def test_agg_count(self):
        """Tests the 'count' aggregation function."""
        grouped = self.df.groupby("Cognitive Status")
        agg_df = grouped.agg({"Donor ID": "count"})

        self.assertIsInstance(agg_df, DataFrame)
        self.assertEqual(agg_df._columns, ["Cognitive Status", "Donor ID_count"])
        # There should be a few cognitive status groups
        self.assertGreater(agg_df._shape[0], 1)
        # The total count should equal the original number of rows
        total_count = sum(agg_df["Donor ID_count"])
        self.assertEqual(total_count, self.df._shape[0])

    def test_agg_max(self):
        """Tests the 'max' aggregation function on a numeric column."""
        grouped = self.df.groupby("Sex")
        agg_df = grouped.agg({"Age at Death": "max"})

        self.assertIsInstance(agg_df, DataFrame)
        self.assertEqual(agg_df._columns, ["Sex", "Age at Death_max"])
        # Should have 'Female' and 'Male' groups
        self.assertIn("Female", agg_df["Sex"])
        self.assertIn("Male", agg_df["Sex"])

        max_ages = agg_df["Age at Death_max"]
        self.assertTrue(
            all(isinstance(age, (int, float)) for age in max_ages if age is not None)
        )

    def test_agg_mean(self):
        """Tests the 'mean' aggregation function."""
        grouped = self.df.groupby("Sex")
        agg_df = grouped.agg({"Age at Death": "mean"})

        self.assertIsInstance(agg_df, DataFrame)
        self.assertEqual(agg_df._columns, ["Sex", "Age at Death_mean"])

        mean_ages = agg_df["Age at Death_mean"]
        # Assert that the calculated means are reasonable (e.g., between 50 and 120)
        for mean_age in mean_ages:
            if mean_age is not None:
                self.assertGreater(mean_age, 50)
                self.assertLess(mean_age, 120)

    def test_agg_multiple_functions(self):
        """Tests applying multiple aggregations in one call."""
        grouped = self.df.groupby("Cognitive Status")
        agg_df = grouped.agg(
            {"Age at Death": "mean", "Years of education": "max", "Donor ID": "count"}
        )

        self.assertIsInstance(agg_df, DataFrame)
        expected_cols = [
            "Cognitive Status",
            "Age at Death_mean",
            "Years of education_max",
            "Donor ID_count",
        ]
        self.assertEqual(agg_df._columns, expected_cols)
        self.assertGreater(agg_df._shape[0], 1)
        self.assertEqual(agg_df._shape[1], 4)
