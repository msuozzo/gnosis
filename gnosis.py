"""An interface for interaction with a Gnosis spreadsheet
"""
from api import sheets_api_login

from datetime import datetime, date, timedelta


class Gnosis(object):
    """Interface for modifying a Gnosis spreadsheet.

    Args:
        credential_path: Local path to the Google API credentials file.
        sheet_key: The Base64 identifier for the target Gnosis spreadsheet.
    """
    INITIALIZER = 'START'
    TIME_FMT = '%a, %m/%d/%y'
    LABEL_ROW = 1
    LABEL_COL = 1
    DATA_START_ROW = 2
    DATA_START_COL = 2

    def __init__(self, credential_path, sheet_key):
        api = sheets_api_login(credential_path)
        self._sheet = api.open_by_key(sheet_key).sheet1

        self._trim()

        label_range = '%s:%s' % (
            self._sheet.get_addr_int(Gnosis.LABEL_ROW, Gnosis.DATA_START_COL),
            self._sheet.get_addr_int(Gnosis.LABEL_ROW, self._sheet.col_count))
        label_cells = self._sheet.range(label_range)
        self._stat_to_col = {cell.value: Gnosis.DATA_START_COL + i
                             for i, cell in enumerate(label_cells, start=1)}

        self._start_date = self._get_date(Gnosis.DATA_START_ROW)
        self._end_date = self._get_date(self._sheet.row_count)

    @staticmethod
    def _parse_date(date_str):
        """Return a `datetime.date` instance from a Gnosis-formatted date
        string.
        """
        try:
            return datetime.strptime(date_str, Gnosis.TIME_FMT).date()
        except ValueError:
            #TODO: Raise custom error
            raise

    @staticmethod
    def _to_date_str(a_date):
        """Return a Gnosis-formatted date from a `datetime.date` instance.
        """
        return date.strftime(a_date, Gnosis.TIME_FMT)

    def _get_date(self, row):
        """Retrieve the date represented by `row`
        WARNING: Triggers an API HTTP request -> SLOW!!

        Return:
            a `date` instance
        """
        date_str = self._sheet.cell(row, Gnosis.LABEL_COL).value
        return Gnosis._parse_date(date_str)

    def _get_approx_date(self, row):
        """Guesses at the date represented by `row` based on its offset from
        the start date.

        This should be preferred over Gnosis._get_approx_date

        Return:
            a `date` instance
        """
        return self._start_date + timedelta(days=row - Gnosis.DATA_START_ROW)

    def _get_row(self, a_date):
        """Return the row index associated with the date `a_date`

        If a_date does not occur
        """
        delta = a_date - self._start_date
        if a_date > self._end_date or a_date < self._start_date:
            raise ValueError
        else:
            return Gnosis.DATA_START_ROW + delta.days

    def _get_or_create_row(self, a_date):
        """Ensure a row associated with `a_date` exists in the backing
        spreadsheet. If it does not, create it.

        Returns:
            The index of the row associate with `a_date`
        """
        try:
            return self._get_row(a_date)
        except ValueError:
            create_before = a_date < self._start_date
            closest_date = self._start_date if create_before else \
                    self._end_date
            rows_to_create = abs(a_date - closest_date).days
            if rows_to_create > 1000:
                raise ValueError('Unable to create more than 1000 rows')

            #TODO: Format the added cells as dates?
            offset_iter = (timedelta(days=i)
                           for i in xrange(1, rows_to_create))
            if create_before:
                #FIXME: Requires a bulk insertion function
                for offset in offset_iter:
                    date_str = Gnosis._to_date_str(closest_date - offset)
                    self._sheet.insert_row([date_str], 2)

                self._start_date = a_date
            else:
                self._sheet.add_rows(rows_to_create)

                base_row = self._sheet.row_count
                new_cells_addr = 'A%d:A%d' % (base_row + 1,
                                              base_row + rows_to_create)
                new_cells = self._sheet.range(new_cells_addr)

                for ind, offset in enumerate(offset_iter):
                    new_cells[ind].value = closest_date + offset
                self._sheet.update_cells(new_cells)

                self._end_date = a_date

            return self._get_row(a_date)

    def _trim(self):
        """Remove unused rows and columns from the spreadsheet

        Only unused rows after the lowest used row and unused columns after
        the right-most used column will be removed.
        """
        row = self._sheet.row_count
        for row, label in reversed(list(self._col_iter(Gnosis.LABEL_COL))):
            if label or row == 1:
                break

        col = self._sheet.col_count
        for col, label in reversed(list(self._row_iter(Gnosis.LABEL_ROW))):
            if label or col == 1:
                break

        self._sheet.resize(rows=row, cols=col)

    def _get_stat_col(self, stat_name):
        """Return the column for stat `stat_name`
        """
        try:
            return self._stat_to_col[stat_name]
        except KeyError:
            raise ValueError

    def _get_coords(self, stat_name, a_date):
        """Return the row and column coordinates of the cell associated with
        stat `stat_name` on date `a_date`

        Returns:
            A 2-tuple of (date_row, stat_col)

        Raises:
            ValueError if `stat_name` cannot be found
        """
        return self._get_row(a_date), self._get_stat_col(stat_name)

    def add_stat_series(self, stat_name):
        """Add a new statistic column with the title `stat_name`

        Args:
            stat_name: The title of the statistic column to be added
        """
        self._sheet.add_cols(1)
        added_col = self._sheet.col_count
        self._sheet.update_cell(Gnosis.LABEL_ROW, added_col, stat_name)
        self._stat_to_col[stat_name] = added_col

        # Add initializer string just above the current day
        yesterday = date.today() - timedelta(days=1)
        init_row = self._get_or_create_row(yesterday)
        self._sheet.update_cell(init_row, added_col, Gnosis.INITIALIZER)

    def update_stat(self, stat_name, a_date, updated_val):
        """Set the value of the cell associated with stat `stat_name` on
        date `a_date` to the value `updated_val`
        """
        date_row, stat_col = self._get_coords(stat_name, a_date)
        self._sheet.update_cell(date_row, stat_col, updated_val)

    def get_stat(self, stat_name, a_date):
        """Return the value of the cell associated with stat `stat_name` on
        date `a_date`
        """
        date_row, stat_col = self._get_coords(stat_name, a_date)
        return self._sheet.cell(date_row, stat_col)

    def get_stat_series(self, stat_name):
        """Return a list of 2-tuples (date, value) associated with stat
        `stat_name`
        """
        return list(self._stat_iter(stat_name))

    def get_stat_start(self, stat_name):
        """Get the start date for the stat `stat_name`

        Returns:
            A date object representing the start date for `stat_name`
        """
        start_date, _ = next(self._stat_iter(stat_name))
        return start_date

    def _row_values(self, row):
        """Return a list of the values in the row `row`
        """
        start = self._sheet.get_addr_int(row, 1)
        end = self._sheet.get_addr_int(row, self._sheet.col_count)
        return [cell.value for cell in self._sheet.range('%s:%s' % (start, end))]

    def _col_values(self, col):
        """Return a list of the values in the column `col`
        """
        start = self._sheet.get_addr_int(1, col)
        end = self._sheet.get_addr_int(self._sheet.row_count, col)
        return [cell.value for cell in self._sheet.range('%s:%s' % (start, end))]

    def _row_iter(self, row):
        """Return an iterator over the values in row `row`

        Args:
            row: The index of the row over which to iterate

        Returns:
            A generator yielding 2-tuples of (col_num, cell_val)
        """
        cell_values = self._row_values(row)
        for row, cell_value in enumerate(cell_values, start=1):
            yield (row, cell_value)

    def _col_iter(self, col):
        """Return an iterator over the values in column `col`

        Args:
            col: The index of the column over which to iterate

        Returns:
            A generator yielding 2-tuples of (row_num, cell_val)
        """
        cell_values = self._col_values(col)
        for row, cell_value in enumerate(cell_values, start=1):
            yield (row, cell_value)

    def _stat_iter(self, stat_name):
        """Return an iterator over the column for `stat_name`.

        Iterator begins on the row following the INITIALIZER row.

        Returns:
            A list of 2-tuples (date, value) for the stat `stat_name`
        """
        has_started = False
        stat_col = self._get_stat_col(stat_name)
        for row, cell in self._col_iter(stat_col):
            if has_started:
                yield (self._get_approx_date(row), cell)
            has_started = has_started or cell == self.INITIALIZER
