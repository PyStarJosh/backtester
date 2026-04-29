import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Processor:
    """Collects & parses financial market data collected by loader.py"""

    db_path = Path(__file__).parent/'financial_data.db' # ensures db is in same dir with processor.py

    def __init__(self):
        self.conn = sqlite3.connect(self.db_path)  # Connection initialization
        self.cur = self.conn.cursor()  # cursor initialization (used for executing actions)
        self._init_tables() # Initializes tables (if not existing)

    # These methods allow me to use the class as a context manager

    def __enter__(self):  # Opens connection
        return self

    def __exit__(self, *args):  # Closes connection
        self.conn.close()


    # Without if not exists, sqlite3 will attempt to recreate the 
    # tables and throw an error since they already exist
    def _init_tables(self):
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS time_series_data(symbol TEXT, interval TEXT, datetime TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER, PRIMARY KEY (symbol, datetime, interval))"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS commodity_prices(interval TEXT, commodity_type TEXT, date TEXT, price REAL, PRIMARY KEY (commodity_type, interval, date))"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS last_updated(symbol TEXT, interval TEXT, start_date TEXT, last_date TEXT, PRIMARY KEY (symbol, interval))"""
        )
        self.conn.commit()

    # TABLE POPULATING METHODS
    
    def populate_time_series_data_table(self, interval, time_series_data_dict, symbol):
        try:
            for value_dict in time_series_data_dict['values']:
                self.cur.execute(
                    """INSERT OR IGNORE INTO time_series_data VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                    (symbol.upper(),
                    interval.lower(),
                    value_dict['datetime'],
                    value_dict['open'],
                    value_dict['high'],
                    value_dict['low'],
                    value_dict['close'],
                    value_dict.get('volume', 0))
                )
            self.conn.commit()
        
            start_date = time_series_data_dict['values'][-1]['datetime']
            last_date = time_series_data_dict['values'][0]['datetime']
            self._populate_last_updated_table(symbol, interval, start_date, last_date)
            
        except sqlite3.OperationalError as op_error:
            logger.critical(f"Database Error: {op_error}")
    
    def populate_commodities_prices_table(self, commodities_data_dict, interval, commodity_type):
        try:
            for data_dict in commodities_data_dict['data']:
                self.cur.execute(
                    '''INSERT OR IGNORE INTO commodity_prices VALUES(?, ?, ?, ?)''', 
                    (interval.lower(),
                    commodity_type.upper(),
                    data_dict['date'],
                    data_dict['value']))
            self.conn.commit()
            
            start_date = commodities_data_dict['data'][-1]['date']
            last_date = commodities_data_dict['data'][0]['date']
            self._populate_last_updated_table(commodity_type, interval, start_date, last_date)
        
        except sqlite3.OperationalError as op_error:
            logger.critical(f'Database Error: {op_error}')
        
    # DATA GETTER METHODS
    
    def get_time_series_data(self, symbol, interval, start_date=None, end_date=None):
        if start_date and end_date:
            self.cur.execute(
                'SELECT * FROM time_series_data WHERE symbol = ? AND interval = ? AND datetime BETWEEN ? AND ?',
                (symbol.upper(), interval.lower(), start_date, end_date)
            )
        elif start_date:
            self.cur.execute(
                'SELECT * FROM time_series_data WHERE symbol = ? AND interval = ? AND datetime >= ?',
                (symbol.upper(), interval.lower(), start_date)
            )
        else:
            self.cur.execute(
                'SELECT * FROM time_series_data WHERE symbol = ? AND interval = ?',
                (symbol.upper(), interval.lower())
            )
            
        unformatted_table_data = self.cur.fetchall()
        return self._format_time_series_data(unformatted_table_data)
    
    def get_commodity_data(self, commodity_type, interval):
        self.cur.execute(
            'SELECT * FROM commodity_prices WHERE commodity_type = ? AND interval = ?',
            (commodity_type.upper(), interval.lower())
        )
            
        unformatted_table_data = self.cur.fetchall()
        return self._format_commodity_data(unformatted_table_data)
  
    def get_last_updated(self, symbol, interval):
        self.cur.execute(
            'SELECT start_date, last_date FROM last_updated WHERE symbol = ? AND interval = ?',
            (symbol.upper(), interval.lower())
        )
        
        dates_tuple = self.cur.fetchone() # fetchone returns a tuple
        return self._format_last_updated_data(dates_tuple) if dates_tuple else None
    
    # HELPER METHODS
    def _populate_last_updated_table(self, symbol, interval, start_date, last_date):
        try:
            stored_dates_dict = self.get_last_updated(symbol, interval)
            if stored_dates_dict:
                new_start =  min(stored_dates_dict['start_date'], start_date)
                new_last = max(stored_dates_dict['last_date'], last_date)
            else:
                new_start = start_date
                new_last = last_date
                
            self.cur.execute(
                'INSERT OR REPLACE INTO last_updated VALUES(?, ?, ? ,?)',
                (symbol.upper(),
                interval.lower(),
                new_start,
                new_last))
            self.conn.commit()
        
        except sqlite3.OperationalError as op_error:
            logger.critical(f'Database Error: {op_error}')
                
    def _format_time_series_data(self, unformatted_table_rows):
        return [
            {
                'symbol': row[0],
                'interval': row[1],
                'datetime':row[2],
                'open': row[3],
                'high': row[4],
                'low': row[5],
                'close': row[6],
                'volume': row[7] 
            }
            for row in unformatted_table_rows
        ]
    
    def _format_commodity_data(self, unformatted_table_rows):
        return [
            {
                'interval': row[0],
                'commodity_type': row[1],
                'date': row[2],
                'price': row[3],                
            }
            for row in unformatted_table_rows
        ]
    
    def _format_last_updated_data(self, dates_tuple):
        return {
            'start_date': dates_tuple[0],
            'last_date': dates_tuple[1]
        }