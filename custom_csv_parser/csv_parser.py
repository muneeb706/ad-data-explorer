from .dataframe import DataFrame


class CSVParser:
    """
    A simple CSV parser that reads a CSV file and converts it into a DataFrame.
    """

    def __init__(self, filepath, separator=","):
        self.filepath = filepath
        self.separator = separator

    def _clean_value(self, value):
        """
         A helper method to strip whitespace and quotes from a value.

        Args:
            value (str): The value to clean.
        Returns:
            str: The cleaned value.
        """
        return value.strip().strip('"')

    def _parse_line(self, line):
        """
        Parses a single line, respecting quoted fields,
        multi value fields separated by separator (e-g ",")
        are expected to be enclosed inside quotes.
        """
        values = []
        current_value = ""
        in_quotes = False

        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == self.separator and not in_quotes:
                values.append(self._clean_value(current_value))
                current_value = ""
            else:
                current_value += char

        # Add the last value after the loop finishes
        values.append(self._clean_value(current_value))
        return values

    def parse(self):
        """
        Parses the CSV file and returns a DataFrame.

        Returns:
            DataFrame: A DataFrame containing the parsed data.

        Raises:
            FileNotFoundError: If the filepath does not exist.
            ValueError: If rows have inconsistent number of columns.
        """
        try:
            with open(self.filepath, "r") as file:
                lines = file.readlines()
                if not lines:
                    return DataFrame({}, [])

                # extract and clean the header row
                header_line = lines[0].strip()
                columns = self._parse_line(header_line)
                num_columns = len(columns)
                data = {col: [] for col in columns}

                # implement the main parsing loop for data rows
                for i, line in enumerate(lines[1:]):
                    if not line.strip():  # Skip empty lines
                        continue

                    values = self._parse_line(line)

                    if len(values) != num_columns:
                        raise ValueError(
                            f"Row {i+2}: Expected {num_columns} columns, but found {len(values)}"
                        )

                    # Append data to the respective column list
                    for col_idx, col_name in enumerate(columns):
                        data[col_name].append(values[col_idx])

                return DataFrame(data, columns)

        except FileNotFoundError:
            print(f"Error: The file at {self.filepath} was not found.")
            raise
        except Exception as e:
            print(f"An error occurred during parsing: {e}")
            raise
