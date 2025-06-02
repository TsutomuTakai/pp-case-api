import pytest
from models import db, User
import time

def test_get_users_empty(client):
    """Testa se retorna uma lista vazia quando não há usuários (após o dump).
    Este teste pode ser ajustado se o dump sempre tiver usuários.
    Se o dump sempre tiver dados, este teste deve verificar a quantidade de dados do dump.
    """
    response = client.get('/v1/users')
    assert response.status_code == 200
    assert len(response.json['items']) > 0 # Agora espera que haja dados do dump (usando 'items' do Smorest)
    assert response.json['total_items'] > 0

def test_add_user_authenticated(auth_client):
    """Testa a adição de um novo usuário com autenticação."""
    response = auth_client.post('/v1/users', json={'name': 'João Silva', 'email': 'joao@example.com', 'password': 'joaopassword'})
    assert response.status_code == 201
    assert response.json['name'] == 'João Silva'
    assert response.json['email'] == 'joao@example.com'
    assert 'id' in response.json

def test_add_user_unauthenticated(client):
    """Testa a adição de um novo usuário sem autenticação (deve falhar)."""
    response = client.post('/v1/users', json={'name': 'João Silva', 'email': 'joao@example.com', 'password': 'joaopassword'})
    assert response.status_code == 401 # Unauthorized
    assert 'Autenticação inválida' in response.json['message'] 

def test_get_single_user(client, auth_client):
    """Testa a recuperação de um usuário específico."""
    response = client.get(f'/v1/users/1')
    assert response.status_code == 200
    assert response.json['name'] == 'Test User'
    assert response.json['email'] == 'primeiro@example.com'

def test_update_user_authenticated(auth_client):
    """Testa a atualização de um usuário existente com autenticação."""
    response = auth_client.put(f'/v1/users/2', json={'name': 'Fulano Atualizado', 'email': 'fulano_novo@example.com'})
    assert response.status_code == 200
    assert response.json['name'] == 'Fulano Atualizado'
    assert response.json['email'] == 'fulano_novo@example.com'

def test_delete_user_authenticated(auth_client):
    """Testa a remoção de um usuário com autenticação."""
    response = auth_client.delete(f'/v1/users/3')
    assert response.status_code == 204
    with auth_client.application.app_context():
        assert not db.session.get(User,3) # Verifica se o usuário foi realmente deletado

def test_add_user_invalid_email(auth_client):
    """Testa a adição de usuário com email inválido."""
    response = auth_client.post('/v1/users', json={'name': 'Teste', 'email': 'invalid-email', 'password': 'testepassword'})
    assert response.status_code == 422
    assert 'Dados de entrada inválidos' in response.json['message']

def test_add_user_duplicate_email(auth_client):
    """Testa a adição de usuário com email duplicado (email 'test@example.com' já existe no dump)."""
    response = auth_client.post('/v1/users', json={'name': 'Outro Duplicado', 'email': 'test@example.com', 'password': 'duppassword'})
    assert response.status_code == 409
    assert 'Um usuário com este e-mail já existe' in response.json['message']

def test_get_users_pagination(client, auth_client):
    """Testa a paginação de usuários."""
    for i in range(10, 20): 
        auth_client.post('/v1/users', json={'name': f'User {i}', 'email': f'user{i}@example.com', 'password': f'pass{i}'})

    # Agora, o total de usuários é 3 (do dump) + 11 (criados aqui) = 14
    response = client.get('/v1/users?page=1&per_page=5')
    assert response.status_code == 200
    assert len(response.json['items']) == 5
    assert response.json['total_items'] == 14 # Total ajustado
    assert response.json['total_pages'] == 3 # 14 usuários / 5 por página = 2.8 -> 3 páginas
    assert response.json['page'] == 1

    response = client.get('/v1/users?page=3&per_page=5')
    assert response.status_code == 200
    assert len(response.json['items']) == 4 # Última página terá 4 usuários (14 - 10)
    assert response.json['page'] == 3

def test_get_users_filter_name(client, auth_client):
    """Testa a filtragem de usuários por nome."""
    response = client.get('/v1/users?name=Fulano')
    assert response.status_code == 200
    assert len(response.json['items']) == 1
    assert response.json['items'][0]['name'] == 'Fulano de Tal'

def test_get_users_sort_email_desc(client, auth_client):
    """Testa a ordenação de usuários por email em ordem decrescente."""
    response = client.get('/v1/users?sort_by=email&order=desc')
    assert response.status_code == 200
    emails = [user['email'] for user in response.json['items']]
    assert emails[0] == 'primeiro@example.com' 
    assert emails[1] == 'fulano@example.com'
    assert emails[2] == 'ciclana@example.com'

def test_login_success(client):
    """Testa o login com credenciais válidas (usuário do dump)."""
    response = client.post('/login', json={'email': 'test@example.com', 'password': 'password'})
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_login_failure(client):
    """Testa o login com credenciais inválidas."""
    response = client.post('/login', json={'email': 'nonexistent@example.com', 'password': 'wrong_password'})
    assert response.status_code == 401
    assert 'Email ou senha inválidos' in response.json['errors'] # Mensagem customizada do JWT loader


def test_rate_limit_get_users(client):
    """Testa se o rate limiting funciona para GET /v1/users/."""
    for _ in range(11): # Exemplo: 10 per minute limit
        response = client.get('/v1/users')
    assert response.status_code == 429 # Too Many Requests

