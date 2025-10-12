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
