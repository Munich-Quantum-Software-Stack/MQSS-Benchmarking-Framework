import os
from os.path import join
from dotenv import load_dotenv


dotenv_path = join(os.getcwd(), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

MQSS_TOKEN = os.getenv("MQSS_TOKEN", "")
MQSS_PORT = os.getenv("MQSS_PORT", "4000")
MQSS_URL = os.getenv("MQSS_URL", "https://portal.quantum.lrz.de")
MQSS_URL = f"{MQSS_URL}:{MQSS_PORT}"
MQSS_BACKEND = os.getenv("MQSS_BACKEND", "QExa20")
