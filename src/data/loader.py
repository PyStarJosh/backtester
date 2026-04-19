import requests
import logging
from ..constants import Constants

# Logger initialization
logger = logging.getLogger(__name__)  # Allows for proper error logging of functions utilizing logging config from main py


class Loader:
    """Loads EOD Data from Financial Data API dating back 10yrs"""

    BASE_URL = "https://www.alphavantage.co/query?"

    SUPPORTED_STOCK_SYMBOLS = {
        "TSLA": [
            {"ratio": 5.0, "date": "2020-08-31"},
            {"ratio": 3.0, "date": "2022-08-25"},
        ],
        "NFLX": {"ratio": 7.0, "date": "2015-07-15"},
        "SHOP": {"ratio": 10.0, "date": "2022-06-29"},
        "AMZN": {"ratio": 20.0, "date": "2022-06-06"},
        "AMD": None,
        "PLTR": None,
        "MARA": None,
        "COIN": None,
        "RIVN": None,
        "LCID": None,
        "SNAP": None,
        "UBER": None,
        "XYZ": None,
        "SOFI": None,
        "RBLX": None,
        "DKNG": None,
        "SPOT": None,
        "ABNB": None,
        "RDDT": None,
        "HOOD": None,
        "U": None,
        "PYPL": None,
        "CRWD": None,
        "NET": None,
        "DDOG": None,
    }

    VALID_COMMODITIES_INTERVALS = {
        "XAU": ["daily", "weekly", "monthly"],
        "XAG": ["daily", "weekly", "monthly"],
        "WTI": ["daily", "weekly", "monthly"],
        "BRENT": ["daily", "weekly", "monthly"],
        "COPPER": ["monthly", "quarterly", "annual"],
        "WHEAT": ["monthly", "quarterly", "annual"],
        "ALUMINUM": ["monthly", "quarterly", "annual"],
        "CORN": ["monthly", "quarterly", "annual"],
        "COTTON": ["monthly", "quarterly", "annual"],
        "SUGAR": ["monthly", "quarterly", "annual"],
        "COFFEE": ["monthly", "quarterly", "annual"],
        "NATURAL_GAS": ["daily", "weekly", "monthly"],
    }

    AV_API_ERROR_RESPONSES = {
        "Error Message": "Invalid API Call",
        "Information": "API Rate Limit Exceeded",
        "Note": "API Rate Limit Exceeded",
    }

    def __init__(self):
        self.__API_KEY = Constants.get_api_key()

    def _get_split_ratio(self, symbol, date):
        split_ratio = 1
        ratio_values = self.SUPPORTED_STOCK_SYMBOLS[symbol.upper()]  # Stores value of supported stock dicts passed symbol key
        
        if ratio_values is None:
            return split_ratio
        
        elif isinstance(ratio_values, dict):
            if date < ratio_values["date"]:
                split_ratio *= ratio_values["ratio"]
        
        elif isinstance(ratio_values, list):
            for ratio_dict in ratio_values:
                if date < ratio_dict["date"]:
                    split_ratio *= ratio_dict["ratio"]
                    
        return split_ratio

    def _adjust_stock_data(self, r, symbol):
        adjusted_stock_data = {}
        
        for date, value in r["Time Series (Daily)"].items():
            adjusted_stock_data[date] = {}
            split_ratio = self._get_split_ratio(symbol.upper(), date) # Calls _get_split_ratio() at each date key for updated split checking
            
            for (price_type, price_data) in value.items():  # Accesses the key-value of the date's value dict
                if price_type == "5. volume":
                    adjusted_volume = int(price_data) * split_ratio
                    adjusted_stock_data[date][price_type] = adjusted_volume
                else:
                    adjusted_stock_price = float(price_data) / split_ratio
                    adjusted_stock_data[date][price_type] = adjusted_stock_price
                    
        return adjusted_stock_data

    def _call_api(self, url, symbol=None):
        try:
            r = requests.get(url, timeout=5)  # Makes HTTP request to Alpha Vantage APi with a timeout of 5 seconds
            r.raise_for_status()
            data_json = r.json()
            
            for key in self.AV_API_ERROR_RESPONSES:
                if key in data_json:
                    raise ValueError(data_json[key])  # Passes Alpha Vantage message to ValueError except block
            
            if symbol and symbol.upper() in self.SUPPORTED_STOCK_SYMBOLS:
                return self._adjust_stock_data(data_json, symbol.upper())
            
            return data_json
        
        except (requests.exceptions.ConnectionError) as http_connection_error:  # Most common error, catches HTTP connection errors
            logger.critical(f"HTTP Connection Error: {http_connection_error}")
            raise
        except (requests.exceptions.Timeout) as http_timeout:  # Catches  HTTP Timeout errors
            logger.critical(f"HTTP Timeout Error: {http_timeout}")
            raise
        except (requests.exceptions.HTTPError) as http_error:  # Catches HTTP unsuccessful status code errors
            logger.critical(f"HTTP Error: {http_error.args[0]}")
            raise
        except requests.exceptions.JSONDecodeError:
            logger.critical("Response was not valid JSON")
            raise
        except ValueError as value_error:
            logger.critical(f"Unsuccessful API Call: {value_error}")
            raise
        except (requests.exceptions.RequestException) as request_error:  # Catches any other HTTP request errors
            logger.critical(f"HTTP Request Error: {request_error}")
            raise

    # Returns a JSON file of raw EOD stock data
    def get_stock_data(self, symbol):
        if symbol.upper() in self.SUPPORTED_STOCK_SYMBOLS:
            url = f"""{self.BASE_URL}function=TIME_SERIES_DAILY&symbol={symbol.upper()}&apikey={self.__API_KEY}"""
            return self._call_api(url, symbol.upper())
        raise ValueError(f"Unsupported Stock Symbol: {symbol.upper()} is not supported")

    # Returns a JSON file of raw EOD forex data
    def get_forex_data(self, from_currency, to_currency):
        url = f"""{self.BASE_URL}function=FX_DAILY&from_symbol={from_currency.upper()}&to_symbol={to_currency.upper()}&apikey={self.__API_KEY}"""
        return self._call_api(url)

    # Returns a JSON file of raw EOD cryptocurrency data
    def get_crypto_data(self, symbol, market):
        url = f"""{self.BASE_URL}function=DIGITAL_CURRENCY_DAILY&symbol={symbol.upper()}&market={market.upper()}&apikey={self.__API_KEY}"""
        return self._call_api(url, symbol)

    # Returns a JSON file of raw EOD Gold data
    def get_gold_data(self, interval):
        if interval.lower() not in self.VALID_COMMODITIES_INTERVALS["XAU"]:
            raise ValueError(f"Unsupported Interval: {interval.lower()} for XAU")

        url = f"""{self.BASE_URL}function=GOLD_SILVER_HISTORY&symbol=XAU&interval={interval.lower()}&apikey={self.__API_KEY}"""
        return self._call_api(url)

    # Returns a JSON file of raw EOD Silver data
    def get_silver_data(self, interval):
        if interval.lower() not in self.VALID_COMMODITIES_INTERVALS["XAG"]:
            raise ValueError(f"Unsupported Interval: {interval.lower()} for XAG")

        url = f"""{self.BASE_URL}function=GOLD_SILVER_HISTORY&symbol=XAG&interval={interval.lower()}&apikey={self.__API_KEY}"""
        return self._call_api(url)

    # Returns a JSON file of raw EOD commodities data (excluding silver and gold)
    def get_commodities_data(self, commodity_type, interval):
        if commodity_type.upper() not in self.VALID_COMMODITIES_INTERVALS:
            raise ValueError(f"Unsupported Commodity Type: {commodity_type}")

        if (interval.lower() not in self.VALID_COMMODITIES_INTERVALS[commodity_type.upper()]):
            raise ValueError(f"Unsupported Interval: {interval.lower()} for {commodity_type.upper()}")

        url = f"""{self.BASE_URL}function={commodity_type.upper()}&interval={interval.lower()}&apikey={self.__API_KEY}"""
        return self._call_api(url)
