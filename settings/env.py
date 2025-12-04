from dotenv import load_dotenv
import os

load_dotenv()

OWM_API = os.getenv("OWM_API")
WEB_IP = os.getenv("WEB_IP", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", 5000))

MONGO_IP = os.getenv("MONGO_IP", "127.0.0.1")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "root")      
MONGO_PASS = os.getenv("MONGO_PASS", "password")  

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "secret")


