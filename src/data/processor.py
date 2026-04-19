import sqlite3  # Attempts to create tables each time it's imported

class Processor:
    """Collects & parses financial market data collected by loader.py"""

    def __init__(self):
        self.conn = sqlite3.connect("financial_data.db")  # Connection initialization
        self.cur = self.conn.cursor()  # cursor initialization (used for executing actions)
        self._init_tables()

    # These methods allow me to use the class as a context manager

    def __enter__(self):  # Opens connection
        return self

    def __exit__(self, *args):  # Closes connection
        self.conn.close()


    # Without if not exists, sqlite3 will attempt to recreate the 
    # tables and throw an error since they already exist
    def _init_tables(self):
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS stock_prices(symbol TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER, PRIMARY KEY (symbol, date))"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS forex_prices(from_currency TEXT, to_currency TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, PRIMARY KEY (from_currency, to_currency, date))"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS crypto_prices(symbol TEXT, market TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER, PRIMARY KEY (symbol, market, date))"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS commodity_prices(interval TEXT, commodity_type TEXT, date TEXT, price REAL, PRIMARY KEY (commodity_type, interval, date))"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS silver_prices(interval TEXT, date TEXT, price REAL, PRIMARY KEY (date, interval))"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS gold_prices(interval TEXT, date TEXT, price REAL, PRIMARY KEY (date, interval))"""
        )
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS last_updated(market_type TEXT, symbol TEXT, last_date TEXT, PRIMARY KEY (market_type, symbol))"""
        )
        self.conn.commit()

    def populate_stock_prices_table(self, stock_data_dict, symbol):
        for date, value_dict in stock_data_dict.items():
            self.cur.execute(
                """INSERT OR IGNORE INTO stock_prices VALUES(?, ?, ?, ?, ?, ?, ?)""",
                (symbol,
                date,
                value_dict["1. open"],
                value_dict["2. high"],
                value_dict["3. low"],
                value_dict["4. close"],
                value_dict["5. volume"])
            )
        self.conn.commit()
        
    def populate_forex_prices_table(self, forex_data_dict, from_currency, to_currency):
        for date, value_dict in forex_data_dict['Time Series FX (Daily)'].items():
            self.cur.execute(
                '''INSERT OR IGNORE INTO forex_prices VALUES(?, ?, ?, ?, ?, ?, ?)''', 
                (from_currency,
                to_currency,
                date,
                value_dict["1. open"],
                value_dict["2. high"],
                value_dict["3. low"],
                value_dict["4. close"]))
        self.conn.commit()
    
    def populate_crypto_prices_table(self, crypto_data_dict, symbol, market):
        for date, value_dict in crypto_data_dict['Time Series (Digital Currency Daily)'].items():
            self.cur.execute(
                '''INSERT OR IGNORE INTO crypto_prices VALUES(?, ?, ?, ?, ?, ?, ?, ?)''', 
                (symbol,
                market,
                date,
                value_dict["1. open"],
                value_dict["2. high"],
                value_dict["3. low"],
                value_dict["4. close"],
                value_dict['5. volume']))
        self.conn.commit()
            
    def populate_silver_prices_table(self, silver_data_dict, interval):
        for data_dict in silver_data_dict['data']:
            self.cur.execute(
                '''INSERT OR IGNORE INTO silver_prices VALUES(?, ?, ?)''', 
                (interval,
                data_dict['date'],
                data_dict['price']))
        self.conn.commit()
            
    def populate_gold_prices_table(self, gold_data_dict, interval):
        for data_dict in gold_data_dict['data']:
            self.cur.execute(
                '''INSERT OR IGNORE INTO gold_prices VALUES(?, ?, ?)''', 
                (interval,
                data_dict['date'],
                data_dict['price']))
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
            (market_type,
             symbol,
             last_date))
        self.conn.commit()
        