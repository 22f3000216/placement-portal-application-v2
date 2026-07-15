from datetime import timedelta
class Config:
    
    SECRET_KEY = "my-secret-key-123"
    SQLALCHEMY_DATABASE_URI = "sqlite:///ppa.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = "my-super-secret-jwt-signing-key-for-placement-portal-2026"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=4)
    
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_HOST = "localhost"
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_DB = 0
    CACHE_DEFAULT_TIMEOUT = 60

    CELERY_BROKER_URL = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/2"

    #MAIL_SERVER = "localhost"
    #MAIL_PORT = 1025
    #MAIL_SENDER = "noreply@placementportal.com"

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_SENDER = "22f3000216@ds.study.iitm.ac.in"       # Gmail address
    MAIL_PASSWORD = "oudj kwvn mwit bftr"     # Gmail App Password

