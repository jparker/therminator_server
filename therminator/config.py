import os

class Base:
    BCRYPT_LOG_ROUNDS = os.getenv('BCRYPT_LOG_ROUNDS', 13)
    DEBUG = os.getenv('FLASK_DEBUG', False)
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class Development(Base):
    BCRYPT_LOG_ROUNDS = os.getenv('BCRYPT_LOG_ROUNDS', 4)
    DEBUG = True
    SECRET_KEY = 'deadbeef'
    SERVER_NAME = 'localhost:5000'

class Test(Base):
    BCRYPT_LOG_ROUNDS = os.getenv('BCRYPT_LOG_ROUNDS', 4)
    DEBUG = True
    SECRET_KEY = 'deadbeef'
    SQLALCHEMY_DATABASE_URI = 'postgres:///therminator_test'
    TESTING = True

class Production(Base):
    pass
