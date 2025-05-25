-- tests/test_data_dump.sql
-- Massa de dados inicial para os testes
-- Certifique-se de que o usuário 'test@example.com' esteja aqui para os testes de autenticação
INSERT INTO user (id, name, email) VALUES (1, 'Test User', 'test@example.com');
INSERT INTO user (id, name, email) VALUES (2, 'Fulano de Tal', 'fulano@example.com');
INSERT INTO user (id, name, email) VALUES (3, 'Ciclana Souza', 'ciclana@example.com');
-- Adicione mais dados conforme necessário para seus cenários de teste
