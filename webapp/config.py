from os import environ

from dotenv import load_dotenv


load_dotenv()


class Config:
    # DEBUG = False
    # TEST = False

    DB_CONNECTION_STRING = environ["AI_DB_CONNECTION_STRING"]
