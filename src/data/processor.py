import sqlite3


class Processor:
    """Collects & parses financial market data collected by loader.py"""

    def __init__(self):
        self.conn = sqlite3.connect("financial_data.db")  # Connection initialization
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
            """CREATE TABLE IF NOT EXISTS time_series_data(market_type TEXT, symbol TEXT, datetime TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER, PRIMARY KEY (market_type, symbol, datetime))"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS commodity_prices(interval TEXT, commodity_type TEXT, date TEXT, price REAL, PRIMARY KEY (commodity_type, interval, date))"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS last_updated(market_type TEXT, symbol TEXT, last_date TEXT, PRIMARY KEY (market_type, symbol))"""
        )
        self.conn.commit()

    # TABLE POPULATING METHODS
    
    def populate_time_series_data_table(self, market_type, time_series_data_dict, symbol):
        for value_dict in time_series_data_dict['values']:
            self.cur.execute(
                """INSERT OR IGNORE INTO time_series_data VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                (market_type.upper(),
                symbol.upper(),
                value_dict['datetime'],
                value_dict['open'],
                value_dict['high'],
                value_dict['low'],
                value_dict['close'],
                value_dict.get('volume', 0))
            )
        self.conn.commit()
    
    def populate_commodities_prices_table(self, commodities_data_dict, interval, commodity_type):
        for data_dict in commodities_data_dict['data']:
            self.cur.execute(
                '''INSERT OR IGNORE INTO commodity_prices VALUES(?, ?, ?, ?)''', 
                (interval.lower(),
                 commodity_type.upper(),
                data_dict['date'],
                data_dict['value']))
        self.conn.commit()
    
    def populate_last_updated_table(self, market_type, symbol, last_date):
        self.cur.execute(
            'INSERT OR REPLACE INTO last_updated VALUES(?, ?, ?)',
            (market_type.upper(),
             symbol.upper(),
             last_date))
        self.conn.commit()
        
    # DATA GETTER METHODS
    
    def get_time_series_data(self, market_type, symbol, start_date=None, end_date=None):
        if start_date and end_date:
            self.cur.execute(
                'SELECT * FROM time_series_data WHERE market_type = ? AND symbol = ? AND datetime BETWEEN ? AND ?',
                (market_type.upper(), symbol.upper(), start_date, end_date)
            )
        elif start_date:
            self.cur.execute(
                'SELECT * FROM time_series_data WHERE market_type = ? AND symbol = ? AND datetime >= ?',
                (market_type.upper(), symbol.upper(), start_date)
            )
        else:
            self.cur.execute(
                'SELECT * FROM time_series_data WHERE market_type = ? AND symbol = ?',
                (market_type.upper(), symbol.upper())
            )
            
        unformatted_table_data = self.cur.fetchall()
        return self._format_time_series_data(unformatted_table_data)
    
    def get_commodity_data(self, commodity_type, interval, start_date=None, end_date=None):
        if start_date and end_date:
            self.cur.execute(
                'SELECT * FROM commodity_prices WHERE commodity_type = ? AND interval = ? AND date BETWEEN ? AND ?',
                (commodity_type.upper(), interval, start_date, end_date)
            )
        elif start_date:
            self.cur.execute(
                'SELECT * FROM commodity_prices WHERE commodity_type = ? AND interval = ? AND date >= ?',
                (commodity_type.upper(), interval.lower(), start_date)
            )
        else:
            self.cur.execute(
                'SELECT * FROM commodity_prices WHERE commodity_type = ? AND interval = ?',
                (commodity_type.upper(), interval.lower())
            )
            
        unformatted_table_data = self.cur.fetchall()
        return self._format_commodity_data(unformatted_table_data)
  
    def get_last_updated(self, market_type, symbol):
        self.cur.execute(
            'SELECT last_date FROM last_updated WHERE market_type = ? AND symbol = ?',
            (market_type.upper(), symbol.upper())
        )
        
        result = self.cur.fetchone() # fetchone returns a tuple
        return result[0] if result else None # returns last date from tuple or None if it does not exist yet
    
    # HELPER METHODS
        
    def _format_time_series_data(self, unformatted_table_rows):
        return [
            {
                'market_type': row[0],
                'symbol': row[1],
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
                'commodity': row[1],
                'date': row[2],
                'price': row[3],                
            }
            for row in unformatted_table_rows
        ]