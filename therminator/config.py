import os

class Base:
    DEBUG = os.getenv('FLASK_DEBUG', False)
    SECRET_KEY = os.environ['SECRET_KEY']

class Development(Base):
    DEBUG = True
    SERVER_NAME = 'localhost:5000'

class Test(Base):
    DEBUG = True
    SECRET_KEY = 'deadbeef'
    TESTING = True

class Production(Base):
    pass
