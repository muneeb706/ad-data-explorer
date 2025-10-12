"""
Unit test suite for pandas-like filter and projection syntax for DataFrame.
"""

import unittest
import os
from custom_csv_parser.csv_parser import CSVParser
from custom_csv_parser.dataframe import DataFrame, Series

# How to run the tests:
# python -m unittest custom_csv_parser.tests.test_csv_filter_and_projection


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

    def setUp(self):
        """
        Set up test data before each test method by parsing the CSV file.
        """
        parser = CSVParser(filepath=self.DONOR_METADATA_FILE)
        self.df = parser.parse()


class TestDataFrameFilterBasic(BaseDataFrameTest):
    """
    Test suite for basic DataFrame filtering operations.
    """

    def test_filter_with_lambda_callable(self):
        """
        Test filtering using callable (lambda) on real data.
        Filter donors with Age at Death > 80
        """
        result = self.df.filter(
            lambda row: row["Age at Death"] and float(row["Age at Death"]) > 80
        )

        self.assertIsInstance(result, DataFrame)
        self.assertGreater(result._shape[0], 0, "Should return at least one row")

        # Verify all ages are greater than 80
        for age in result._data["Age at Death"]:
            if age:  # Skip empty values
                self.assertGreater(float(age), 80)

    def test_pandas_filter_sex_equality(self):
        """
        Test pandas-like syntax with equality comparison: df[df['Sex'] == 'Female']
        """
        result = self.df[self.df["Sex"] == "Female"]

        self.assertIsInstance(result, DataFrame)
        self.assertGreater(
            result._shape[0], 0, "Should return at least one female donor"
        )

        # Verify all returned rows are Female
        for sex in result._data["Sex"]:
            self.assertEqual(sex, "Female")

    def test_pandas_filter_sex_inequality(self):
        """
        Test pandas-like syntax with inequality comparison: df[df['Sex'] != 'Female']
        """
        result = self.df[self.df["Sex"] != "Female"]

        self.assertIsInstance(result, DataFrame)
        self.assertGreater(
            result._shape[0], 0, "Should return at least one non-female donor"
        )

        # Verify no Female in results
        for sex in result._data["Sex"]:
            self.assertNotEqual(sex, "Female")

    def test_pandas_filter_cognitive_status(self):
        """
        Test filtering by Cognitive Status: df[df['Cognitive Status'] == 'Dementia']
        """
        result = self.df[self.df["Cognitive Status"] == "Dementia"]

        self.assertIsInstance(result, DataFrame)

        if result._shape[0] > 0:
            # Verify all returned rows have Dementia status
            for status in result._data["Cognitive Status"]:
                self.assertEqual(status, "Dementia")

    def test_filter_apoe_genotype(self):
        """
        Test filtering by APOE Genotype: df[df['APOE Genotype'] == 'E3/E3']
        """
        result = self.df[self.df["APOE Genotype"] == "E3/E3"]

        self.assertIsInstance(result, DataFrame)

        if result._shape[0] > 0:
            # Verify all returned rows have E3/E3 genotype
            for genotype in result._data["APOE Genotype"]:
                self.assertEqual(genotype, "E3/E3")

    def test_filter_primary_study_name(self):
        """
        Test filtering by Primary Study Name
        """
        result = self.df[self.df["Primary Study Name"] == "ACT"]

        self.assertIsInstance(result, DataFrame)

        if result._shape[0] > 0:
            # Verify all returned rows are from ACT study
            for study in result._data["Primary Study Name"]:
                self.assertEqual(study, "ACT")

    def test_filter_race_field(self):
        """
        Test filtering by race field: df[df['Race (choice=White)'] == 'Checked']
        """
        result = self.df[self.df["Race (choice=White)"] == "Checked"]

        self.assertIsInstance(result, DataFrame)

        if result._shape[0] > 0:
            # Verify all returned rows have White race checked
            for race_value in result._data["Race (choice=White)"]:
                self.assertEqual(race_value, "Checked")

    def test_filter_no_matching_rows(self):
        """
        Test filtering that returns no matching rows.
        """
        result = self.df[self.df["Sex"] == "NonExistentSex"]

        self.assertIsInstance(result, DataFrame)
        self.assertEqual(result._shape[0], 0, "Should return 0 rows")
        self.assertEqual(
            result._shape[1], self.df._shape[1], "Should have same number of columns"
        )

    def test_filter_preserves_original_dataframe(self):
        """
        Test that filtering doesn't modify the original DataFrame.
        """
        original_shape = self.df._shape
        original_donor_ids = list(self.df._data["Donor ID"])

        # Apply filter
        _ = self.df[self.df["Sex"] == "Female"]

        # Verify original is unchanged
        self.assertEqual(self.df._shape, original_shape)
        self.assertEqual(self.df._data["Donor ID"], original_donor_ids)


class TestDataFrameFilterAdvanced(BaseDataFrameTest):
    """
    Test suite for advanced DataFrame filtering operations.
    """

    def test_combined_conditions_sex_and_cognitive_status(self):
        """
        Test combined conditions: Female donors with Dementia
        Sex == 'Female' AND Cognitive Status == 'Dementia'
        """
        sex_mask = self.df["Sex"] == "Female"
        cognitive_mask = self.df["Cognitive Status"] == "Dementia"
        combined_mask = [s and c for s, c in zip(sex_mask, cognitive_mask)]
        result = self.df[combined_mask]

        self.assertIsInstance(result, DataFrame)

        if result._shape[0] > 0:
            # Verify all rows match both conditions
            for sex, status in zip(
                result._data["Sex"], result._data["Cognitive Status"]
            ):
                self.assertEqual(sex, "Female")
                self.assertEqual(status, "Dementia")

    def test_filter_multiple_conditions_with_or_logic(self):
        """
        Test filtering with OR logic using lambda.
        Filter donors that are either Female OR have Dementia
        """
        result = self.df.filter(
            lambda row: row["Sex"] == "Female" or row["Cognitive Status"] == "Dementia"
        )

        self.assertIsInstance(result, DataFrame)
        self.assertGreater(result._shape[0], 0, "Should return at least one row")


class TestDataFrameProjection(BaseDataFrameTest):
    """
    Test suite for DataFrame projection (column selection) operations.
    """

    def test_projection_single_column(self):
        """
        Test projecting a single column returns a Series.
        """
        result = self.df["Donor ID"]

        self.assertIsInstance(result, Series)
        self.assertEqual(len(result), self.df._shape[0])
        self.assertEqual(result._name, "Donor ID")

    def test_projection_multiple_columns(self):
        """
        Test projecting multiple columns from real data.
        """
        columns_to_select = ["Donor ID", "Sex", "Age at Death"]
        result = self.df[columns_to_select]

        self.assertIsInstance(result, DataFrame)
        self.assertEqual(
            result._shape[0], self.df._shape[0], "Should have same number of rows"
        )
        self.assertEqual(result._shape[1], 3, "Should have 3 columns")
        self.assertEqual(result._columns, columns_to_select)

    def test_projection_missing_single_column(self):
        """
        Test that projecting a non-existent single column raises KeyError.
        """
        with self.assertRaises(KeyError) as context:
            _ = self.df["NonExistentColumn"]

        self.assertIn("not found", str(context.exception))
        self.assertIn("NonExistentColumn", str(context.exception))

    def test_projection_missing_multiple_columns(self):
        """
        Test that projecting with non-existent columns raises KeyError.
        """
        with self.assertRaises(KeyError) as context:
            _ = self.df[["Donor ID", "NonExistentColumn1", "NonExistentColumn2"]]

        self.assertIn("not found", str(context.exception))
        # Verify the error message includes the missing column names
        error_msg = str(context.exception)
        self.assertTrue(
            "NonExistentColumn1" in error_msg or "NonExistentColumn2" in error_msg
        )

    def test_projection_all_missing_columns(self):
        """
        Test that projecting with all non-existent columns raises KeyError.
        """
        with self.assertRaises(KeyError) as context:
            _ = self.df[["FakeCol1", "FakeCol2", "FakeCol3"]]

        self.assertIn("not found", str(context.exception))

    def test_projection_mixed_valid_and_invalid_columns(self):
        """
        Test that projecting with a mix of valid and invalid columns raises KeyError
        and reports only the missing columns.
        """
        with self.assertRaises(KeyError) as context:
            _ = self.df[["Donor ID", "InvalidColumn", "Sex", "AnotherInvalidColumn"]]

        error_msg = str(context.exception)
        self.assertIn("not found", error_msg)
        # Should mention the invalid columns
        self.assertIn("InvalidColumn", error_msg)
        self.assertIn("AnotherInvalidColumn", error_msg)


class TestDataFrameChainedOperations(BaseDataFrameTest):
    """
    Test suite for chained DataFrame operations (filter + projection, etc.).
    """

    def test_chained_filter_and_projection(self):
        """
        Test chaining filter and projection:
        df[df['Sex'] == 'Female'][['Donor ID', 'Age at Death', 'Cognitive Status']]
        """
        result = self.df[self.df["Sex"] == "Female"][
            ["Donor ID", "Age at Death", "Cognitive Status"]
        ]

        self.assertIsInstance(result, DataFrame)
        self.assertEqual(result._shape[1], 3, "Should have 3 columns")
        self.assertEqual(
            result._columns, ["Donor ID", "Age at Death", "Cognitive Status"]
        )

        if result._shape[0] > 0:
            # Verify we only have the projected columns
            self.assertIn("Donor ID", result._data)
            self.assertIn("Age at Death", result._data)
            self.assertIn("Cognitive Status", result._data)
            self.assertNotIn("Sex", result._data)

    def test_filter_then_project_with_missing_column(self):
        """
        Test that projecting a missing column after filtering raises KeyError.
        """
        filtered_df = self.df[self.df["Sex"] == "Female"]

        with self.assertRaises(KeyError) as context:
            _ = filtered_df[["Donor ID", "NonExistentColumn"]]

        self.assertIn("not found", str(context.exception))
        self.assertIn("NonExistentColumn", str(context.exception))

    def test_head_then_filter(self):
        """
        Test chaining head() and filter operations.
        """
        result = self.df.head(20)[self.df.head(20)["Sex"] == "Female"]

        self.assertIsInstance(result, DataFrame)
        # Result should be <= 20 rows and only females
        self.assertLessEqual(result._shape[0], 20)


class TestSeriesOperations(BaseDataFrameTest):
    """
    Test suite for Series operations and comparisons.
    """

    def test_filter_returns_series_object(self):
        """
        Test that accessing a column returns a Series object.
        """
        sex_series = self.df["Sex"]
        self.assertIsInstance(sex_series, Series)
        self.assertEqual(len(sex_series), self.df._shape[0])
        self.assertEqual(sex_series._name, "Sex")

    def test_series_comparison_returns_boolean_list(self):
        """
        Test that Series comparison operations return boolean lists.
        """
        sex_mask = self.df["Sex"] == "Female"

        self.assertIsInstance(sex_mask, list)
        self.assertEqual(len(sex_mask), self.df._shape[0])
        self.assertTrue(all(isinstance(x, bool) for x in sex_mask))


class TestDataFrameIndexingErrors(BaseDataFrameTest):
    """
    Test suite for DataFrame indexing error handling.
    """

    def test_invalid_column_name(self):
        """
        Test that accessing non-existent column raises KeyError.
        """
        with self.assertRaises(KeyError) as context:
            _ = self.df["NonExistentColumn"]

        self.assertIn("not found", str(context.exception))

    def test_unsupported_indexing_with_integer(self):
        """
        Test that indexing with an integer raises TypeError.
        """
        with self.assertRaises(TypeError) as context:
            _ = self.df[0]

        self.assertIn("Unsupported indexing type", str(context.exception))

    def test_unsupported_indexing_with_slice(self):
        """
        Test that indexing with a slice raises TypeError.
        """
        with self.assertRaises(TypeError) as context:
            _ = self.df[0:5]

        self.assertIn("Unsupported indexing type", str(context.exception))

    def test_unsupported_indexing_with_tuple(self):
        """
        Test that indexing with a tuple of non-booleans raises TypeError.
        """
        with self.assertRaises(TypeError) as context:
            _ = self.df[("Donor ID", "Sex")]

        self.assertIn("Unsupported indexing type", str(context.exception))

    def test_unsupported_indexing_with_dict(self):
        """
        Test that indexing with a dictionary raises TypeError.
        """
        with self.assertRaises(TypeError) as context:
            _ = self.df[{"column": "Donor ID"}]

        self.assertIn("Unsupported indexing type", str(context.exception))

    def test_unsupported_indexing_with_none(self):
        """
        Test that indexing with None raises TypeError.
        """
        with self.assertRaises(TypeError) as context:
            _ = self.df[None]

        self.assertIn("Unsupported indexing type", str(context.exception))

    def test_unsupported_indexing_with_set(self):
        """
        Test that indexing with a set raises TypeError.
        """
        with self.assertRaises(TypeError) as context:
            _ = self.df[{"Donor ID", "Sex"}]

        self.assertIn("Unsupported indexing type", str(context.exception))

    def test_list_with_mixed_types(self):
        """
        Test that indexing with a list containing mixed types (not all booleans or strings)
        raises appropriate error.
        """
        with self.assertRaises((TypeError, KeyError)):
            _ = self.df[["Donor ID", True, 123]]


class TestBooleanMaskValidation(BaseDataFrameTest):
    """
    Test suite for boolean mask validation and error handling.
    """

    def test_boolean_mask_length_mismatch_too_short(self):
        """
        Test that a boolean mask shorter than the DataFrame raises ValueError.
        """
        num_rows = self.df._shape[0]
        short_mask = [True, False, True]  # Only 3 elements

        with self.assertRaises(ValueError) as context:
            _ = self.df[short_mask]

        error_msg = str(context.exception)
        self.assertIn("Boolean mask length", error_msg)
        self.assertIn("does not match", error_msg)
        self.assertIn(str(len(short_mask)), error_msg)
        self.assertIn(str(num_rows), error_msg)

    def test_boolean_mask_length_mismatch_too_long(self):
        """
        Test that a boolean mask longer than the DataFrame raises ValueError.
        """
        num_rows = self.df._shape[0]
        long_mask = [True] * (num_rows + 10)  # 10 more elements than needed

        with self.assertRaises(ValueError) as context:
            _ = self.df[long_mask]

        error_msg = str(context.exception)
        self.assertIn("Boolean mask length", error_msg)
        self.assertIn("does not match", error_msg)
        self.assertIn(str(len(long_mask)), error_msg)
        self.assertIn(str(num_rows), error_msg)

    def test_filter_with_mixed_boolean_and_non_boolean(self):
        """
        Test that passing a list with mixed boolean and non-boolean values raises TypeError.
        """
        num_rows = self.df._shape[0]
        mixed_mask = [True, False, "True", 1] + [False] * (num_rows - 4)

        with self.assertRaises(TypeError) as context:
            _ = self.df[mixed_mask]

        error_msg = str(context.exception)
        self.assertIn("all elements must be booleans", error_msg)

    def test_filter_method_with_boolean_mask_length_mismatch(self):
        """
        Test that calling filter() method directly with mismatched boolean mask raises ValueError.
        """
        short_mask = [True, False, True]

        with self.assertRaises(ValueError) as context:
            _ = self.df.filter(short_mask)

        error_msg = str(context.exception)
        self.assertIn("Boolean mask length", error_msg)
        self.assertIn("does not match", error_msg)

    def test_filter_method_with_non_boolean_list(self):
        """
        Test that calling filter() method with non-boolean list raises TypeError.
        """
        num_rows = self.df._shape[0]
        non_bool_list = [1, 0, 1] * (num_rows // 3 + 1)
        non_bool_list = non_bool_list[:num_rows]  # Exact length

        with self.assertRaises(TypeError) as context:
            _ = self.df.filter(non_bool_list)

        error_msg = str(context.exception)
        self.assertIn("all elements must be booleans", error_msg)

    def test_filter_with_invalid_condition_type(self):
        """
        Test that passing an invalid condition type (not list/tuple/callable) raises TypeError.
        """
        with self.assertRaises(TypeError) as context:
            _ = self.df.filter("not a valid condition")

        error_msg = str(context.exception)
        self.assertIn("Condition must be", error_msg)

    def test_filter_with_tuple_boolean_mask(self):
        """
        Test that filter works with tuple boolean masks (not just lists).
        """
        num_rows = self.df._shape[0]
        tuple_mask = tuple([True if i % 2 == 0 else False for i in range(num_rows)])

        result = self.df.filter(tuple_mask)

        self.assertIsInstance(result, DataFrame)
        # Should return approximately half the rows
        expected_count = sum(tuple_mask)
        self.assertEqual(result._shape[0], expected_count)
