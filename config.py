import os
from dotenv import load_dotenv

load_dotenv() # Carrega as variáveis de ambiente do arquivo .env

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') 
    RESTX_MASK_SWAGGER = False # Para exibir todos os campos no Swagger UI
    # Configuração de paginação padrão
    PER_PAGE = 10
    # Configuração para Flask-Limiter
    LIMITER_DEFAULT_LIMIT = "200 per day"
    LIMITER_STORAGE_URI = "memory://" # Para SQLite, você pode usar 'sqlite:///limiter.db'
    # Configuração para Flask-Caching
    CACHE_TYPE = "SimpleCache" # Ou "RedisCache", "MemcachedCache" etc.
    CACHE_DEFAULT_TIMEOUT = 300 # Segundos

class TestConfig(Config): # Herda de Config para manter outras configurações
    TESTING = True # Indica que a aplicação está em modo de teste
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Usa banco de dados SQLite em memória
    # Desativa logging e cache para testes para evitar saída excessiva
    LIMITER_ENABLED = False
    CACHE_TYPE = "NullCache" # Desativa o cache durante os testes
    # Outras configurações específicas para testes, se necessário
