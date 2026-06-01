from os import environ

from dotenv import load_dotenv


load_dotenv()


class Config:
    # DEBUG = False
    # TEST = False

    SECRET_KEY = environ["SECRET_KEY"]
