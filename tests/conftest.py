# tests/conftest.py
import pytest
from app import create_app
from models import db, User
from config import TestConfig # Importa a configuração de teste
import os
from sqlalchemy import text # Importar 'text' para executar SQL raw

@pytest.fixture(scope='session')
def app():
    """Cria e configura uma nova instância do app para cada sessão de teste,
    usando o banco de dados em memória."""
    app = create_app(config_object=TestConfig) # Passa a configuração de teste

    with app.app_context():
        # db.create_all() já é chamado dentro de create_app() se for em memória.
        # Aqui, garantimos que as tabelas sejam criadas para a sessão de teste.
        db.create_all()
        yield app
        db.drop_all() # Limpa o banco de dados em memória após a sessão de teste

@pytest.fixture(scope='function')
def client(app):
    """Um cliente de teste para fazer requisições, garantindo um DB limpo e populado para cada teste."""
    with app.app_context():
        db.drop_all() # Limpa as tabelas existentes
        db.create_all() # Recria as tabelas para um estado limpo

        # --- CARREGAR MASSA DE DADOS ESPECÍFICA PARA TESTES ---
        # Caminho para o arquivo SQL de dump
        dump_file_path = os.path.join(os.path.dirname(__file__), 'test_data_dump.sql')
        if os.path.exists(dump_file_path):
            with open(dump_file_path, 'r') as f:
                sql_script = f.read()
            db.session.execute(text(sql_script)) # Executa o script SQL no banco de dados em memória
            db.session.commit()
        # --- FIM DA CARGA DE DADOS ---

        yield app.test_client() # Retorna o cliente de teste

@pytest.fixture(scope='function')
def auth_client(app):
    """Um cliente de teste com token de autenticação, garantindo um DB limpo e usuário de teste."""
    with app.app_context():
        db.drop_all()
        db.create_all()

        # --- CARREGAR MASSA DE DADOS ESPECÍFICA PARA TESTES ---
        dump_file_path = os.path.join(os.path.dirname(__file__), 'test_data_dump.sql')
        if os.path.exists(dump_file_path):
            with open(dump_file_path, 'r') as f:
                sql_script = f.read()
            db.session.execute(text(sql_script))
            db.session.commit()
        # --- FIM DA CARGA DE DADOS ---

        # O usuário 'test@example.com' deve estar presente no test_data_dump.sql
        # Se não estiver, você pode criá-lo aqui programaticamente:
        # test_user = User.query.filter_by(email='test@example.com').first()
        # if not test_user:
        #     test_user = User(name='Test User', email='test@example.com')
        #     db.session.add(test_user)
        #     db.session.commit()

    with app.test_client() as client:
        # Login para obter o token (assumindo que 'test@example.com' existe e tem senha 'password')
        response = client.post('/login', json={'email': 'test@example.com', 'password': 'password'})
        # Adiciona verificação para garantir que o login foi bem-sucedido
        if response.status_code != 200:
            raise Exception(f"Falha ao fazer login no fixture auth_client: {response.json}")
        token = response.json['access_token']
        client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        yield client
