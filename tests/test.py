# tests/test_users.py
import pytest
from models import db, User
import time

def test_get_users_empty(client):
    """Testa se retorna uma lista vazia quando não há usuários (após o dump).
    Este teste pode ser ajustado se o dump sempre tiver usuários.
    Se o dump sempre tiver dados, este teste deve verificar a quantidade de dados do dump.
    """
    response = client.get('/v1/users/')
    assert response.status_code == 200
    # Ajuste este assert se o dump sempre tiver dados
    assert len(response.json['users']) > 0 # Agora espera que haja dados do dump
    assert response.json['total_users'] > 0

def test_add_user_authenticated(auth_client):
    """Testa a adição de um novo usuário com autenticação."""
    response = auth_client.post('/v1/users/', json={'name': 'João Silva', 'email': 'joao@example.com'})
    assert response.status_code == 201
    assert response.json['name'] == 'João Silva'
    assert response.json['email'] == 'joao@example.com'
    assert 'id' in response.json

def test_add_user_unauthenticated(client):
    """Testa a adição de um novo usuário sem autenticação (deve falhar)."""
    response = client.post('/v1/users/', json={'name': 'João Silva', 'email': 'joao@example.com'})
    assert response.status_code == 401 # Unauthorized
    assert 'Missing JWT' in response.json['msg']

def test_get_single_user(client, auth_client):
    """Testa a recuperação de um usuário específico."""
    # O usuário com ID 1 deve vir do test_data_dump.sql
    response = client.get(f'/v1/users/1')
    assert response.status_code == 200
    assert response.json['name'] == 'Test User'
    assert response.json['email'] == 'test@example.com'

def test_update_user_authenticated(auth_client):
    """Testa a atualização de um usuário existente com autenticação."""
    # Atualiza um usuário que veio do dump (e.g., ID 2)
    response = auth_client.put(f'/v1/users/2', json={'name': 'Fulano Atualizado', 'email': 'fulano_novo@example.com'})
    assert response.status_code == 200
    assert response.json['name'] == 'Fulano Atualizado'
    assert response.json['email'] == 'fulano_novo@example.com'

def test_delete_user_authenticated(auth_client):
    """Testa a remoção de um usuário com autenticação."""
    # Deleta um usuário que veio do dump (e.g., ID 3)
    response = auth_client.delete(f'/v1/users/3')
    assert response.status_code == 204
    with auth_client.application.app_context():
        assert not User.query.get(3) # Verifica se o usuário foi realmente deletado

def test_add_user_invalid_email(auth_client):
    """Testa a adição de usuário com email inválido."""
    response = auth_client.post('/v1/users/', json={'name': 'Teste', 'email': 'invalid-email'})
    assert response.status_code == 400
    assert 'Requisição inválida' in response.json['message']

def test_add_user_duplicate_email(auth_client):
    """Testa a adição de usuário com email duplicado (email 'test@example.com' já existe no dump)."""
    response = auth_client.post('/v1/users/', json={'name': 'Outro Duplicado', 'email': 'test@example.com'})
    assert response.status_code == 409
    assert 'Email já cadastrado' in response.json['message']

def test_get_users_pagination(client, auth_client):
    """Testa a paginação de usuários."""
    # Adicione mais usuários para ter um total maior que o padrão de per_page
    for i in range(4, 15): # Começa do ID 4 para não conflitar com o dump
        auth_client.post('/v1/users/', json={'name': f'User {i}', 'email': f'user{i}@example.com'})

    # Agora, o total de usuários é 3 (do dump) + 11 (criados aqui) = 14
    response = client.get('/v1/users/?page=1&per_page=5')
    assert response.status_code == 200
    assert len(response.json['users']) == 5
    assert response.json['total_users'] == 14 # Total ajustado
    assert response.json['total_pages'] == 3 # 14 usuários / 5 por página = 2.8 -> 3 páginas
    assert response.json['current_page'] == 1
    assert response.json['has_next'] is True

    response = client.get('/v1/users/?page=3&per_page=5')
    assert response.status_code == 200
    assert len(response.json['users']) == 4 # Última página terá 4 usuários (14 - 10)
    assert response.json['current_page'] == 3
    assert response.json['has_next'] is False

def test_get_users_filter_name(client, auth_client):
    """Testa a filtragem de usuários por nome."""
    # Os usuários do dump já servem para este teste
    response = client.get('/v1/users/?name=Test User')
    assert response.status_code == 200
    assert len(response.json['users']) == 1
    assert response.json['users'][0]['name'] == 'Test User'

def test_get_users_sort_email_desc(client, auth_client):
    """Testa a ordenação de usuários por email em ordem decrescente."""
    # Os usuários do dump já servem para este teste
    response = client.get('/v1/users/?sort_by=email&order=desc')
    assert response.status_code == 200
    emails = [user['email'] for user in response.json['users']]
    # Espera-se que os emails estejam em ordem decrescente
    assert emails[0] == 'test@example.com' # 'test' vem antes de 'fulano' e 'ciclana' na ordem alfabética inversa
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
    assert 'Email ou senha inválidos' in response.json['msg']

def test_protected_endpoint(auth_client):
    """Testa o acesso a um endpoint protegido com token válido."""
    response = auth_client.get('/protected')
    assert response.status_code == 200
    assert response.json['hello'] == 'from protected endpoint'

def test_protected_endpoint_no_token(client):
    """Testa o acesso a um endpoint protegido sem token."""
    response = client.get('/protected')
    assert response.status_code == 401
    assert 'Missing JWT' in response.json['msg']

# Testes de Rate Limiting (desativados em conftest, mas úteis para testes manuais)
# def test_rate_limit_get_users(client):
#     """Testa se o rate limiting funciona para GET /v1/users/."""
#     for _ in range(11): # 10 per minute limit
#         response = client.get('/v1/users/')
#     assert response.status_code == 429 # Too Many Requests

# Testes de Cache (desativados em conftest, mas úteis para testes manuais)
# def test_cache_get_users(client, auth_client):
#     """Testa se o cache funciona para GET /v1/users/."""
#     # Adiciona um usuário para garantir que há dados
#     auth_client.post('/v1/users/', json={'name': 'Cached User', 'email': 'cached@example.com'})
#     response1 = client.get('/v1/users/')
#     time.sleep(1) # Pequeno delay para garantir que o cache está ativo
#     # Adiciona outro usuário, mas a resposta deve vir do cache
#     auth_client.post('/v1/users/', json={'name': 'Another User', 'email': 'another@example.com'})
#     response2 = client.get('/v1/users/')
#     assert response1.json == response2.json # Resposta deve ser a mesma devido ao cache
#     time.sleep(60) # Espera o cache expirar
#     response3 = client.get('/v1/users/')
#     assert response1.json != response3.json # Resposta deve ser diferente após o cache expirar
