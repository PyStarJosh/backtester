import logging

# Logger initialization and configuration
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.DEBUG,
)