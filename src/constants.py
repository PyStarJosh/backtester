import os
from dotenv import load_dotenv

load_dotenv()

class Constants():
    @staticmethod # This allow the method to be called without instantiating the class
    def get_api_key(): # Returns API Key
        return os.getenv("ALPHAVANTAGE_API_KEY")
    