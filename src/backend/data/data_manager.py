
import logging
from .processor import Processor
from .loader import Loader

logger = logging.getLogger(__name__)

class DataManager:
    """Coordinates the fetching and storing of data from API to SQLite Database and returns formatted data dict"""

    def __init__(self):
        self.processor = Processor()
        self.loader = Loader()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.processor.conn.close()
        
    def get_formatted_time_series_data(self, symbol, interval, start_date=None, end_date=None):
        dates_dict = self.processor.get_last_updated(symbol, interval)
        if dates_dict is None:
            time_series_data_dict = self.loader.get_time_series_data(symbol, interval)
            self.processor.populate_time_series_data_table(interval, time_series_data_dict, symbol)
            return self.processor.get_time_series_data(symbol, interval, start_date, end_date)     
                        
        stored_start_date, stored_last_date = dates_dict['start_date'], dates_dict['last_date']
        needs_fetch, fetch_start, fetch_end = self._get_missing_range(stored_start_date, stored_last_date, start_date, end_date)
        
        if needs_fetch:
            time_series_data_dict = self.loader.get_time_series_data(symbol, interval, fetch_start, fetch_end)
            self.processor.populate_time_series_data_table(interval, time_series_data_dict, symbol)
        return self.processor.get_time_series_data(symbol, interval, start_date, end_date)                   
    
    def get_formatted_commodities_data(self, commodity_type, interval):
        commodities_data_dict = self.loader.get_commodities_data(commodity_type, interval)
        self.processor.populate_commodities_prices_table(commodities_data_dict, interval, commodity_type)
        return self.processor.get_commodity_data(commodity_type, interval)

    # HELPER METHODS
    
    def _get_missing_range(self, stored_start_date, stored_last_date, start_date, end_date):
        if stored_start_date <= start_date and end_date <= stored_last_date:
            return False, None, None
        elif (stored_start_date <= start_date) and (end_date > stored_last_date):
            return True, stored_last_date, end_date
        elif (stored_start_date > start_date) and (end_date <= stored_last_date):
            return True, start_date, stored_start_date
        else: 
            return True, None, None