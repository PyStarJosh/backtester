from .processor import Processor
from .loader import Loader


class DataManager:
    """Coordinates the fetching and storing of data from API to SQLite Database"""

    def __init__(self):
        self.processor = Processor()
        self.loader = Loader()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.processor.conn.close()
