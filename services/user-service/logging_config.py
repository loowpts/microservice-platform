import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('user_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
