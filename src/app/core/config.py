import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

"""
reference： https://pydantic-docs.helpmanual.io/usage/settings/
            https://myapollo.com.tw/zh-tw/python-pydantic/


1. Arguments passed to the Settings class initializer.
2. Environment variables, e.g. my_prefix_special_function as described above.
3. Variables loaded from a dotenv (.env) file.
4. Variables loaded from the secrets directory.
5. The default field values for the Settings model.
"""


ENV_PATH = os.path.join(
    os.path.dirname(os.path.dirname((os.path.dirname(os.path.abspath(__file__))))),
    ".env",
)


load_dotenv(ENV_PATH)


class Settings(BaseSettings):
    # The URL at which the base of the API will be exposed to the end user
    API_V1_STR: str = "/api/v1"
    API_EXTERNAL_BASE: str = "http://localhost:8000" + API_V1_STR

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    TITLE: str = "SCOT"
    DESCRIPTION: str = "SCOT API"
    DOCS_URL: str | None = None
    OPENAPI_URL: str | None = None
    REDOC_URL: str | None = None
    PROJECT_NAME: str = "SCOT4 API"

    # The database URL used to connect to the database (required)
    SQLALCHEMY_DATABASE_URI: str
    # Database connection settings
    DB_CONNECT_TIMEOUT: int = 100000
    DB_CONNECTION_POOL_SIZE: int = 10
    # this is the amount *over* the pool size, not total
    DB_CONNECTION_POOL_OVERFLOW: int = 20 
    # Will be set to True when running unit tests
    TEST: bool = False
    # The key used to sign JWT tokens (required)
    SECRET_KEY: str
    # Whether or not to generate database data on startup (for testing)
    GENERATE_DATA: bool = False
    # Whether or not secure cookies should be used (set to True in production)
    SECURE_AUTH_COOKIE: bool = False
    # How many reverse proxy steps are between the API and the user
    # Used with the X-Forwarded-For header for user logging
    NUM_TRUSTED_PROXIES: int | None = None

    # Test email (used in tests only)
    EMAIL_TEST_USER: str = "test1@example.com"
    # Starting superuser info (only matters on first database creation)
    FIRST_SUPERUSER: str = "scot-admin@example.com"
    FIRST_SUPERUSER_USERNAME: str = "scot-admin"
    FIRST_SUPERUSER_PASSWORD: str = "EHPVNY9YrQjB8VwD7Gu6H4ebCf"
    FIRST_SUPERUSER_APIKEY: str = ""
    # Settings for emailing users (disabled by default)
    USERS_OPEN_REGISTRATION: bool = False
    EMAILS_ENABLED: bool = False
    MAX_FAILED_PASSWORD_ATTEMPTS: int = 5
    PASSWORD_LOCKOUT_MINUTES: int = 15
    EMAIL_TEMPLATES_DIR: str = "templates"
    # The id of the "everyone" role which includes all users by default
    # Set to None to disable the everyone role
    EVERYONE_ROLE_ID: int | None = 1

    # SMTP options for outgoing email
    SMTP_TLS: bool = True
    SMTP_PORT: int | None = None
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None

    # Flair configuration (required if using the flair engine)
    FLAIR_HOST: str | None = None
    FLAIR_API_FLAIR_ENDPOINT: str | None = "/api/v1/flair"
    FLAIR_API_REGEX_ENDPOINT: str | None = "/api/v1/regex"
    FLAIR_API_KEY: str | None = None

    # Airflow enrichment configuration
    ENRICHMENT_API_JOB_ENDPOINT: str | None = None
    ENRICHMENT_HOST: str | None = None
    ENRICHMENT_USERNAME: str | None = None
    ENRICHMENT_PASSWORD: str | None = None
    ENRICHMENT_TYPES: str | None = None

    MAX_ENRICHMENT_BY_NAME: int = 5

    # Search indexing configuration
    SEARCH_HOST: str | None = ""
    SEARCH_API_KEY: str | None = None

    # Constants for documentation endpoints
    DOCS_URL = "/api/docs"
    OPENAPI_URL: str | None = "/api/openapi.json"
    REDOC_URL: str | None = "/api/redoc"
    SWAGGER_JS_URL: str | None = "/api/static/swagger-ui-bundle.js"
    SWAGGER_CSS_URL: str | None = "/api/static/swagger-ui.css"
    REDOC_JS_URL: str | None = "/api/static/redoc.standalone.js"

    # Settings for email password resets
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None

    # Settings for default file storage provider (enabled by default)
    CREATE_DEFAULT_STORAGE_PROVIDER: bool = True
    FILE_STORAGE_LOCATION: str | None = "/var/scot_files"
    FILE_DELETED_LOCATION: str | None = "/var/scot_files/_deleted_items"

    model_config = SettingsConfigDict(env_file="ENV_PATH", case_sensitive=True)


class Production(Settings):
    """
    Settings for a production deployment of SCOT

    To enable, set environment variable "ENV" to "PROD"
    """
    DEBUG: bool = False
    ENV: str = "Production"
    SECURE_AUTH_COOKIE: bool = True


class Development(Settings):
    """
    Settings for a development/qual deployment of SCOT

    Enabled by default
    """
    DEBUG: bool = True
    ENV: str = "Development"
    FLAIR_API_KEY: str = "myflairapikey"
    FIRST_SUPERUSER_APIKEY: str = "mytestkey"
    API_V1_STR: str = "/api/v1"
    API_EXTERNAL_BASE: str = "http://localhost:7778" + API_V1_STR


class Test(Development):
    """
    Settings for a test build of SCOT (used in unit tests)

    To enable, set environment variable "ENV" to "TEST"
    """
    TEST: bool = True
    SECRET_KEY: str = "scot-secret-key"  # nosec
    GENERATE_DATA: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite://"
    ENV: str = "Test"
    # disable flair
    FLAIR_HOST: str | None = None
    FLAIR_API_FLAIR_ENDPOINT: str | None = None
    FLAIR_API_KEY: str | None = None


def get_settings():
    env: str = os.getenv("ENV")
    if env == "PROD":
        return Production()
    elif env == "TEST":
        return Test()
    return Development()


settings = get_settings()
