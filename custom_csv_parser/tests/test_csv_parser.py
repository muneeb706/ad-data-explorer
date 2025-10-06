import unittest
import os

# The '..' in the import path tells Python to look in the parent directory
# (custom_csv_parser) to find the 'parsers' and 'dataframe' modules.
from ..csv_parser import CSVParser
from ..dataframe import DataFrame

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

        print(df._data["If other Consensus dx, describe"])
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
