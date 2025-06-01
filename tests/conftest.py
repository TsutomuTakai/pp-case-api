import pytest
from app import create_app
from models import db, User, bcrypt_obj
from config import TestConfig
import os
from sqlalchemy import text
import sys


@pytest.fixture(scope='session')
def app():
    app = create_app(config_object=TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    with app.app_context():
        db.drop_all()
        db.create_all()

        dump_file_path = os.path.join(os.path.dirname(__file__), 'test_data_dump.sql')
        if os.path.exists(dump_file_path):
            with open(dump_file_path, 'r') as f:
                sql_script = f.read()
            
            # Arquivo .sql está separando os comandos por ; para facilitar a depuração
            statements = [s.strip() for s in sql_script.split(';') if s.strip()]
            
            for statement in statements:
                try:
                    db.session.execute(text(statement))
                except Exception as e:
                    raise 
            
            db.session.commit()
        
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            test_user = User(name='Test User', email='test@example.com')
            test_user.set_password('password')
            db.session.add(test_user)
            db.session.commit()
        else:
            print("conftest.py: client fixture - test_user já existe", file=sys.stderr)


        yield app.test_client() # Retorna o cliente de teste

@pytest.fixture(scope='function')
def auth_client(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        dump_file_path = os.path.join(os.path.dirname(__file__), 'test_data_dump.sql')
        if os.path.exists(dump_file_path):
            with open(dump_file_path, 'r') as f:
                sql_script = f.read()
            
            statements = [s.strip() for s in sql_script.split(';') if s.strip()]
            for statement in statements:
                try:
                    db.session.execute(text(statement))
                except Exception as e:
                    raise

            db.session.commit()
        
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            test_user = User(name='Test User', email='test@example.com')
            test_user.set_password('password')
            db.session.add(test_user)
            db.session.commit()
        else:
            print("conftest.py: auth_client fixture - test_user já existe", file=sys.stderr)

    with app.test_client() as client:
        response = client.post('/login', json={'email': 'test@example.com', 'password': 'password'})
        if response.status_code != 200:
            raise Exception(f"Falha ao fazer login no fixture auth_client: {response.json}")
        token = response.json['access_token']
        client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        yield client
