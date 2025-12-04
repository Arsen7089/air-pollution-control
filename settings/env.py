from dotenv import load_dotenv
import os

load_dotenv()

OWM_API = os.getenv("OWM_API")
WEB_IP = os.getenv("WEB_IP")
WEB_PORT = os.getenv("WEB_PORT")
MONGO_IP = os.getenv("MONGO_IP")
MONGO_PORT = os.getenv("MONGO_PORT")

