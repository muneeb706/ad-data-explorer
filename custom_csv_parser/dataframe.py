class Series:
    """
    A Series represents a single column from a DataFrame.
    Supports comparison operations that return boolean masks for pandas-like filtering.
    """

    def __init__(self, data, name, parent_df):
        """
        Args:
            data (list): The column data
            name (str): The column name
            parent_df (DataFrame): Reference to parent DataFrame
        """
        self._data = data
        self._name = name
        self._parent_df = parent_df

    def __repr__(self):
        return f"Series(name='{self._name}', length={len(self._data)})"

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, index):
        return self._data[index]

    # Comparison operators that return boolean masks
    def __eq__(self, other):
        """Element-wise equality comparison."""
        return [val == other for val in self._data]

    def __ne__(self, other):
        """Element-wise inequality comparison."""
        return [val != other for val in self._data]

    def __gt__(self, other):
        """Element-wise greater than comparison."""
        return [val > other if val is not None else False for val in self._data]

    def __ge__(self, other):
        """Element-wise greater than or equal comparison."""
        return [val >= other if val is not None else False for val in self._data]

    def __lt__(self, other):
        """Element-wise less than comparison."""
        return [val < other if val is not None else False for val in self._data]

    def __le__(self, other):
        """Element-wise less than or equal comparison."""
        return [val <= other if val is not None else False for val in self._data]

    def to_list(self):
        """Returns the underlying data as a list."""
        return list(self._data)


class DataFrame:
    """
    A custom DataFrame class to store and manipulate tabular data.
    Supports pandas-like syntax for filtering and projection operations.

    Filtering Syntax:
    1. Boolean mask (list of booleans):
       mask = [True, False, True, False]
       df[mask]
    2. Comparison operations on columns:
       df[df['Age'] > 30]
       df[df['City'] == 'NYC']
       df[df['Salary'] >= 50000]
    3. Lambda/function conditions:
       df.filter(lambda row: row['Age'] > 30)
       df.filter(lambda row: row['City'] == 'NYC' and row['Age'] > 25)

    Projection Syntax:
    1. Single column selection (returns a Series):
       df['Age']                    # Returns Series object
       df['City']                   # Returns Series object
    2. Multiple column selection (returns a DataFrame):
       df[['Name', 'Age']]          # Returns DataFrame with 2 columns
       df[['City', 'State', 'Zip']] # Returns DataFrame with 3 columns

    Combined Operations:
    Chain filtering and projection:
    Filter then project
    df[df['Age'] > 30][['Name', 'City']]

    # Project then filter (on projected columns)
    subset = df[['Name', 'Age', 'City']]
    subset[subset['Age'] > 30]

    Supported Comparison Operators:
    - `==` (equal)
    - `!=` (not equal)
    - `>` (greater than)
    - `>=` (greater than or equal)
    - `<` (less than)
    - `<=` (less than or equal)

    Note: Combining multiple conditions with `&` (AND) or `|` (OR) Currently not supported:
    df[(df['Age'] > 30) & (df['City'] == 'NYC')]
    df[(df['Age'] < 25) | (df['Age'] > 65)]
    Workaround:
    Use lambda functions:
    df.filter(lambda row: row['Age'] > 30 and row['City'] == 'NYC')
    df.filter(lambda row: row['Age'] < 25 or row['Age'] > 65)

    Grouping and Aggregation:
    grouped = df.groupby('Sex')
            agg_df = grouped.agg({
                'Age at Death': 'max',
                'Donor ID': 'count'
            })
    Note:
    Currently, this implementation only supports grouping by a single column.
    Multi-column grouping (e.g., groupby(['Sex', 'Cognitive Status'])) is not supported.

    Join Operations:
    1. Inner Join (only supported join type):
       # Join on same column name
       result = df1.join(df2, left_on='ID', right_on='ID')

       # Join on different column names
       result = df1.join(df2, left_on='PersonID', right_on='DonorID')

    2. Join Features:
       - Supports 1-to-1, 1-to-many, and many-to-many relationships
       - Handles column name collisions with _left and _right suffixes
       - Deduplicates join keys when they have the same name
       - Inner join semantics: only includes matching rows

    3. Column Naming Rules:
       - When column exists in both DataFrames:
         * If it's the join key with same name → appears once in result
         * If it's the join key with different name → both versions appear
         * If it's a non-key column → gets _left and _right suffixes

       Example:
       left_df: columns = ['ID', 'Name', 'Score']
       right_df: columns = ['ID', 'Name', 'Grade']
       result = left_df.join(right_df, 'ID', 'ID')
       result columns = ['ID', 'Name_left', 'Score', 'Name_right', 'Grade']

    Limitations:
    - Only inner join is supported (left, right, outer joins not implemented)
    - Join keys must exist in both DataFrames
    - Only single-column joins are supported (composite keys not supported)
    """

    def __init__(self, data, columns):
        self._data = data
        self._columns = columns

        if self._data and self._columns:
            # Determine the number of rows from the length of the first column's list
            self._shape = (len(self._data[self._columns[0]]), len(self._columns))
        else:
            self._shape = (0, 0)

    def __repr__(self):
        return f"DataFrame(shape={self._shape}, columns={self._columns})"

    def __getitem__(self, item):
        """
        Supports:
            - df['colname'] -> returns a Series-like list of values in that column
            - df[['col1', 'col2', ...]] -> returns a new DataFrame with only those columns
            - df[boolean_mask] -> returns a new DataFrame with filtered rows (pandas-like)
        """
        if isinstance(item, str):
            # Single column - return as Series
            # e-g df['col1']
            if item not in self._columns:
                raise KeyError(f"Column '{item}' not found in DataFrame.")
            return Series(self._data[item], item, self)

        elif isinstance(item, list):
            # Check if it's a boolean mask
            # should be of same length as number of rows
            # e-g [True, False, True, ...]
            if item and isinstance(item[0], bool):
                return self.filter(item)

            # Multiple columns
            # e-g df[['col1', 'col2', 'col3']]
            missing_cols = [c for c in item if c not in self._columns]
            if missing_cols:
                raise KeyError(f"Columns {missing_cols} not found in DataFrame.")
            new_data = {col: self._data[col] for col in item}
            return DataFrame(new_data, item)

        else:
            raise TypeError("Unsupported indexing type.")

    def head(self, n=5):
        """
        Returns the first n rows as a new DataFrame.
        Args:
            n (int): The number of rows to return.
        Returns:
            DataFrame: A new DataFrame containing the first n rows.
        """
        # Slice the data for each column to get the first n items
        head_data = {col: self._data[col][:n] for col in self._columns}
        return DataFrame(head_data, self._columns)

    def to_dict(self):
        """
        Returns the DataFrame's data as a standard Python dictionary.
        """
        return self._data

    def filter(self, condition):
        """
        Filters the DataFrame based on a condition.
        Args:
            condition: Can be one of the following:
                - A list/tuple of booleans (boolean mask) - pandas-like syntax
                - A function/lambda that takes a row (dict) and returns True/False
        Returns:
            DataFrame: A new DataFrame containing only the rows that meet the condition.
        Examples:
            # Boolean mask (pandas-like)
            df.filter([True, False, True, ...])
            # Using callable
            df.filter(lambda row: row['age'] > 30)
        """
        num_rows = self._shape[0]

        # Check if condition is a boolean mask (list/tuple of booleans)
        if isinstance(condition, (list, tuple)):
            if len(condition) != num_rows:
                raise ValueError(
                    f"Boolean mask length ({len(condition)}) does not match "
                    f"DataFrame length ({num_rows})"
                )

            # Validate that it's actually a boolean mask
            if not all(isinstance(x, bool) for x in condition):
                raise TypeError(
                    "When passing a list/tuple, all elements must be booleans"
                )

            indices_to_keep = [i for i, keep in enumerate(condition) if keep]

        # Check if condition is callable (function/lambda)
        elif callable(condition):
            indices_to_keep = []
            for i in range(num_rows):
                row = {col: self._data[col][i] for col in self._columns}
                if condition(row):
                    indices_to_keep.append(i)

        else:
            raise TypeError(
                "Condition must be a boolean mask (list/tuple) or a callable (function/lambda)"
            )

        new_data = {
            col: [self._data[col][i] for i in indices_to_keep] for col in self._columns
        }

        return DataFrame(new_data, self._columns)

    def groupby(self, by):
        """
        Groups the DataFrame by a specified column.

        Args:
            by (str): The name of the column to group by.

        Returns:
            DataFrameGroupBy: An object representing the grouped data,
                              ready for an aggregation step.
        """
        if by not in self._columns:
            raise KeyError(f"Column '{by}' not found in DataFrame.")

        grouped_data = {}
        grouping_col_data = self._data[by]

        # Find the unique values in the grouping column to form the groups
        unique_groups = sorted(list(set(grouping_col_data)))

        for group in unique_groups:
            # For each unique group, create a boolean mask to filter the original DataFrame
            mask = [val == group for val in grouping_col_data]
            # self[mask] will use the filtering logic in __getitem__
            # which returns a new DataFrame with only the rows for that group
            grouped_data[group] = self[mask]
            # Example of grouped_data if unique_groups = ['Female', 'Male']
            # ├── 'Female' → DataFrame with 2 rows
            # │   ├── Sex: ['Female', 'Female']
            # │   ├── Age: [30, 28]
            # │   └── City: ['LA', 'LA']
            # │
            # └── 'Male' → DataFrame with 3 rows
            #     ├── Sex: ['Male', 'Male', 'Male']
            #     ├── Age: [25, 35, 40]
            #     └── City: ['NYC', 'NYC', 'Boston']

        return DataFrameGroupBy(grouped_data, by)

    def join(self, right_df, left_on, right_on, how="inner"):
        """
        Joins this DataFrame with another DataFrame (right_df).
        Currently supports 'inner' join.
        Supports 1-to-many and many-to-many relationships.

        Args:
            right_df (DataFrame): The other DataFrame to join with.
            left_on (str): The key column name in this (left) DataFrame.
            right_on (str): The key column name in the right_df.
            how (str): The type of join. Currently only 'inner' is supported.

        Returns:
            DataFrame: A new DataFrame containing the joined data.

        Example:
            left = DataFrame({'ID': ['A', 'B'], 'Value': [1, 2]}, ['ID', 'Value'])
            right = DataFrame({'ID': ['A', 'B'], 'Name': ['X', 'Y']}, ['ID', 'Name'])
            result = left.join(right, 'ID', 'ID')
            # Result: DataFrame with columns ['ID', 'Value', 'Name']
        """

        # INPUT VALIDATION
        # Type checking: ensure right_df is a DataFrame object
        if not isinstance(right_df, DataFrame):
            raise TypeError("right_df must be a DataFrame object")

        # Type checking: ensure join key column names are strings
        if not isinstance(left_on, str) or not isinstance(right_on, str):
            raise TypeError("left_on and right_on must be strings")

        # Ensure only supported join type is requested (inner join only)
        if how != "inner":
            raise ValueError(
                f"Join type '{how}' not supported. Only 'inner' is implemented."
            )

        # Verify that the join key columns exist in both DataFrames
        # This prevents KeyError when trying to access non-existent columns later
        if left_on not in self._columns:
            raise KeyError(f"Column '{left_on}' not found in left DataFrame.")
        if right_on not in right_df._columns:
            raise KeyError(f"Column '{right_on}' not found in right DataFrame.")

        # BUILD HASH INDEX FOR RIGHT DATAFRAME
        # Purpose: Enable O(1) lookup of right DataFrame rows by join key value
        # Time Complexity: O(n) where n = number of rows in right DataFrame
        # Space Complexity: O(n)
        #
        # This is a critical optimization: instead of nested loops (O(n*m)),
        # a hash map is built that allows us to find matching rows in O(1) time.
        #
        # Structure:
        #   right_index = {
        #       'value1': [row_idx1, row_idx2, ...],  # Multiple rows with same key
        #       'value2': [row_idx3],                  # Single row with this key
        #       ...
        #   }

        right_index = {}
        right_key_data = right_df[right_on]  # Get the join key column as a Series

        # Iterate through each row index and corresponding key value in right DataFrame
        for i, key_val in enumerate(right_key_data):
            # Initialize a list for this key value if not seen before
            # This list will store ALL row indices that have this key value
            # (supports many-to-many joins where multiple rows share same key)
            if key_val not in right_index:
                right_index[key_val] = []

            # Append the current row index to the list for this key value
            right_index[key_val].append(i)

        # PREPARE NEW DATAFRAME STRUCTURE
        # Purpose: Set up the schema (columns) and data containers for the result
        # This step handles column name collisions by adding suffixes (_left, _right)
        #
        # Strategy:
        #   1. Add all left columns first (with _left suffix if collision)
        #   2. Add all right columns (with _right suffix if collision, skip join key if duplicate)
        #   3. Initialize empty lists for each column to hold result data

        new_data = {}  # Dictionary: column_name -> list of values
        new_columns = []  # List: maintains column order for result DataFrame

        # Add LEFT columns to the result schema
        # Include all columns from the left DataFrame
        # If a column exists in both DataFrames AND it's not a join key, add "_left" suffix
        for col in self._columns:
            new_col_name = col

            # Check if this column name also exists in right DataFrame
            # AND it's not one of the join key columns (to avoid confusion about join keys)
            if col in right_df._columns and col != left_on and col != right_on:
                new_col_name = f"{col}_left"

            # Add the column to result schema
            new_columns.append(new_col_name)
            new_data[new_col_name] = []  # Initialize empty list for values

        # Add RIGHT columns to the result schema
        # Include all columns from the right DataFrame (except join key if it's a duplicate)
        for col in right_df._columns:
            # Skip the join key column ONLY if it has the same name in both DataFrames
            # (already have it from the left side; don't need to add it twice)
            if col == right_on and left_on == right_on:
                continue

            new_col_name = col

            # Check if this column name also exists in left DataFrame
            # AND it's not a join key (join keys handled separately)
            if col in self._columns and col != left_on and col != right_on:
                new_col_name = f"{col}_right"

            # Avoid duplicate column initialization
            # (in rare cases where column was already added with suffix)
            if new_col_name not in new_columns:
                new_columns.append(new_col_name)
                new_data[new_col_name] = []

        # PERFORM THE JOIN (ITERATE AND MATCH)
        # Purpose: For each row in left DataFrame, find matching rows in right DataFrame
        #          and append combined data to result
        # Time Complexity: O(n + sum of matches) where n = left DataFrame rows
        #
        # For INNER JOIN:
        #   - Only include rows where key value exists in BOTH DataFrames
        #   - If one left row matches multiple right rows → multiple result rows (many-to-many)
        #   - If one left row has no match → that row is skipped (inner join behavior)

        left_key_data = self._data[
            left_on
        ]  # Get the join key column from left DataFrame

        # Iterate through each row in the left DataFrame
        for left_idx, left_key_val in enumerate(left_key_data):
            # Look up this key value in the right DataFrame index
            # If the key value is not found → skip this row (inner join semantics)
            if left_key_val in right_index:

                # Get ALL row indices from right DataFrame that have this key value
                matching_right_indices = right_index[left_key_val]

                # For each matching right row, create ONE result row
                # This loop handles many-to-many joins:
                #   If one left row matches 3 right rows → creates 3 result rows
                for right_idx in matching_right_indices:

                    # --------
                    # Append all left columns for this left row
                    # --------
                    # Copy all column values from the matching left row into result
                    for col in self._columns:
                        new_col_name = col

                        # Use the suffixed column name if collision exists
                        if (
                            col in right_df._columns
                            and col != left_on
                            and col != right_on
                        ):
                            new_col_name = f"{col}_left"

                        # Append the value from this left row
                        new_data[new_col_name].append(self._data[col][left_idx])

                    # --------
                    # Append all right columns for this right row
                    # --------
                    # Copy all column values from the matching right row into result
                    for col in right_df._columns:
                        # Skip the join key column ONLY if it has the same name in both DataFrames
                        # (already added it from left side; don't duplicate)
                        # If left_on != right_on, we need to include the right key column, this is in case of joins on different column names
                        if col == right_on and left_on == right_on:
                            continue

                        new_col_name = col

                        # Use the suffixed column name if collision exists
                        if col in self._columns and col != left_on and col != right_on:
                            new_col_name = f"{col}_right"

                        # Append the value from this right row
                        # (check that column was initialized)
                        if new_col_name in new_data:
                            new_data[new_col_name].append(
                                right_df._data[col][right_idx]
                            )

        # Combine all the accumulated data and column definitions into a new DataFrame
        return DataFrame(new_data, new_columns)


class DataFrameGroupBy:
    """
    An intermediate object representing a grouped DataFrame.
    This object is created by DataFrame.groupby() and is used to perform aggregations.
    """

    def __init__(self, grouped_data, by_column):
        self._grouped_data = grouped_data
        self._by_column = by_column

    def __repr__(self):
        return f"DataFrameGroupBy(by='{self._by_column}', ngroups={len(self._grouped_data)})"

    def agg(self, agg_dict):
        """
        Performs aggregation on the grouped data.

        Args:
            agg_dict (dict): A dictionary mapping column names to aggregation functions.
                             Supported functions: 'max', 'min', 'mean', 'count'.
                             Example: {'Age at Death': 'max', 'Donor ID': 'count'}

        Returns:
            DataFrame: A new DataFrame with the aggregated results. The grouping
                       column will become the first column.
                       Example output: DataFrame(shape=(2, 4), columns=['Sex', 'Age at Death_max', 'Donor ID_count', 'Brain Weight_mean'])
                       Internal data structure:
                        {
                            'Sex': ['Female', 'Male'],
                            'Age at Death_max': [92.0, 95.0],
                            'Donor ID_count': [3, 3],
                            'Brain Weight_mean': [1160.0, 1200.0]
                        }

        """
        agg_results = {self._by_column: list(self._grouped_data.keys())}
        result_columns = [self._by_column]

        for col, func_name in agg_dict.items():
            new_col_name = f"{col}_{func_name}"
            result_columns.append(new_col_name)
            agg_results[new_col_name] = []

            for group_name, group_df in self._grouped_data.items():
                column_data = group_df[col]  # This is a Series

                # Convert to numeric if possible for numeric operations
                numeric_data = []
                if func_name in ["max", "min", "mean"]:
                    for val in column_data:
                        try:
                            numeric_data.append(float(val))
                        except (ValueError, TypeError):
                            continue  # Skip non-numeric values

                if func_name == "max":
                    result = max(numeric_data) if numeric_data else None
                elif func_name == "min":
                    result = min(numeric_data) if numeric_data else None
                elif func_name == "mean":
                    result = (
                        sum(numeric_data) / len(numeric_data) if numeric_data else None
                    )
                elif func_name == "count":
                    result = len(column_data)
                else:
                    raise ValueError(f"Unsupported aggregation function '{func_name}'")

                agg_results[new_col_name].append(result)

        return DataFrame(agg_results, result_columns)
