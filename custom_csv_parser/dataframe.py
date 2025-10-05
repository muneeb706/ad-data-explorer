class DataFrame:
    """
    A custom DataFrame class to store and manipulate tabular data.
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
