import os
from dotenv import load_dotenv
from datetime import timedelta 

load_dotenv() # Carrega as variáveis de ambiente do arquivo .env 


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuração do JWT 
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-de-fallback'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'uma-chave-jwt-muito-secreta-de-fallback'

    # Swagger
    API_TITLE = "API de Usuários e Autenticação" # Título
    API_VERSION = "v1" # Versão 
    OPENAPI_VERSION = "3.0.2" # Versão OpenAPI
    OPENAPI_URL_PREFIX = "/" # OpenAPI  (/openapi.json)
    OPENAPI_SWAGGER_UI_PATH = "/docs" # Swagger UI
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/" #arquivos do Swagger UI
    OPENAPI_REDOC_PATH = "/redoc" # ReDoc 
    OPENAPI_REDOC_URL = "https://cdn.jsdelivr.net/npm/redoc@2.0.0-rc.5/bundles/redoc.standalone.js" # Arquivos do ReDoc
    API_SPEC_OPTIONS = {
        'security':[{"bearerAuth": []}],
        'components':{
            "securitySchemes":
                {
                    "bearerAuth": {
                        "type":"http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
        }
    }

    # Configuração de paginação 
    PER_PAGE = 10

    # Limiter 
    LIMITER_DEFAULT_LIMIT = "200 per day"
    LIMITER_STORAGE_URI = "memory://"

    # Cache
    CACHE_TYPE = "SimpleCache" # "RedisCache".
    CACHE_DEFAULT_TIMEOUT = 300 # Segundos

class TestConfig(Config): # Herda de Config para manter outras configurações
    TESTING = True # Indica que a aplicação está em modo de teste
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Usa banco de dados SQLite em memória