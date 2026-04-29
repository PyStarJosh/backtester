import requests
import logging
from ..constants import Constants

# Logger initialization
logger = logging.getLogger(__name__)  # Allows for proper error logging of functions utilizing logging config from main py


class Loader:
    """Loads EOD Data from Financial Data API dating back 10yrs"""

    ALPHAVANTAGE_BASE_URL = 'https://www.alphavantage.co/query?'
    TWELVEDATA_BASE_URL = 'https://api.twelvedata.com/'

    TWELVEDATA_ASSET_TYPES = [
        'stocks',
        'forex_pairs',
        'cryptocurrencies',
    ]
    
    TWELVEDATA_INTERVALS = [
        '1min',
        '5min',
        '15min',
        '30min',
        '45min',
        '1h',
        '2h',
        '4h',
        '8h',
        '1day',
        '1week',
        '1month',
    ]

    VALID_COMMODITIES_INTERVALS = {
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

    API_ERROR_RESPONSES = {
        #Alpha Vantage Error Keys
        "Error Message": "Invalid API Call",
        "Information": "API Rate Limit Exceeded",
        "Note": "API Rate Limit Exceeded",
        
        # Twelve Data Error Keys
        'code': 'Error Status Code',
        'message': 'Error Message',
    }

    def __init__(self):
        self.__ALPHAVANTAGE_API_KEY = Constants.get_alphavantage_api_key()
        self.__TWELVEDATA_API_KEY = Constants.get_twelvedata_api_key()
        
    # Provides dict of all Twelve Data supported symbols
    def get_supported_symbols(self, asset_type):
        if asset_type.lower() not in self.TWELVEDATA_ASSET_TYPES:
            raise ValueError(
                f'Unsupported Asset Type: Twelve Data does not support {asset_type.lower()}'
            )
        
        url = f'''{self.TWELVEDATA_BASE_URL}{asset_type.lower()}?apikey={self.__TWELVEDATA_API_KEY}'''
        return self._call_api(url)
    
    # Returns a python onject of stock, forex, silver, gold, or crypto data
    def get_time_series_data(self, symbol, interval, start_date=None, end_date=None):
        if interval.lower() not in self.TWELVEDATA_INTERVALS:
            raise ValueError(
                f'Unsupported Interval: {interval.lower()} is not supported for {symbol.upper()}'
            )
            
        if not (start_date or end_date):
            url = f"""{self.TWELVEDATA_BASE_URL}time_series?symbol={symbol.upper()}&interval={interval.lower()}&outputsize=5000&adjust=all&apikey={self.__TWELVEDATA_API_KEY}"""
        elif start_date and not end_date:
            url = f"""{self.TWELVEDATA_BASE_URL}time_series?symbol={symbol.upper()}&interval={interval.lower()}&outputsize=5000&adjust=all&start_date={start_date}&apikey={self.__TWELVEDATA_API_KEY}"""
        else:
            url = f"""{self.TWELVEDATA_BASE_URL}time_series?symbol={symbol.upper()}&interval={interval.lower()}&outputsize=5000&adjust=all&start_date={start_date}&end_date={end_date}&apikey={self.__TWELVEDATA_API_KEY}"""

        return self._call_api(url)

    # Returns a python object of commodities data (excluding silver and gold)
    def get_commodities_data(self, commodity_type, interval):
        if commodity_type.upper() not in self.VALID_COMMODITIES_INTERVALS:
            raise ValueError(f"Unsupported Commodity Type: {commodity_type}")

        if (interval.lower() not in self.VALID_COMMODITIES_INTERVALS[commodity_type.upper()]):
            raise ValueError(f"Unsupported Interval: {interval.lower()} for {commodity_type.upper()}")

        url = f"""{self.ALPHAVANTAGE_BASE_URL}function={commodity_type.upper()}&interval={interval.lower()}&apikey={self.__ALPHAVANTAGE_API_KEY}"""
        return self._call_api(url)
    
    # HELPER METHOD

    def _call_api(self, url):
        try:
            r = requests.get(url, timeout=5)  # Makes HTTP request to APi with a timeout of 5 seconds
            r.raise_for_status()
            data_json = r.json()
            if not data_json:
                raise ValueError('API returned empty response')
            
            for key in self.API_ERROR_RESPONSES:
                if key in data_json:
                    raise ValueError(data_json[key]) # Passes Alpha Vantage message to ValueError except block
            
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