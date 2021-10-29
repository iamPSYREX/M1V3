# (c) @AbirHasan2005

import os
import logging

logging.basicConfig(
    format='%(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('log.txt'),
              logging.StreamHandler()],
    level=logging.INFO
)


class Config(object):
    API_ID = int(os.environ.get("API_ID", "7188176"))
    API_HASH = os.environ.get("API_HASH", "00354ec58538f2518bfcb45537a182e2")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "2059559304:AAExYYU30Gn4vSw-6_5_F9R763h07ETLugw")
    LOGGER = logging
