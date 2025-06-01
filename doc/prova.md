# API de Usuários - Teste
Repositório para etapa de avaliação

## Objetivo

Desenvolver uma aplicação web usando o framework Flask para realizar operações CRUD (Create, Read, Update, Delete) em uma entidade de "Usuário". O candidato deve persistir os dados no banco de dados SQLite.

##  Requisitos Técnicos
1. Utilizar Flask (ou FastAPI) como framework.
2. Utilizar o conceito de orientação a objetos no desenvolvimento da aplicação.
3. Persistir os dados em um banco de dados SQLite.
4. Implementar as operações CRUD para a entidade "Usuário" (GET, POST, PUT, DELETE).
5. Implementar testes unitários
6. O código deve ser bem estruturado e seguir as melhores práticas de programação.

## Instruções:
1. Crie um repositório no Git: https://github.com/seuusuario/seu-repositorio.git e clone o
mesmo para a sua máquina local.
2. Crie um ambiente virtual: `python -m venv venv`
3. Ative o ambiente virtual:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`
4. Instale as dependências: `pip install flask`
5. Implemente a aplicação dentro do diretório clonado.
6. Teste a aplicação localmente para garantir seu funcionamento.
7. Prepare uma apresentação (slides, por exemplo) demonstrando a funcionalidade da
aplicação e a persistência dos dados no banco SQLite.

## Endpoints:
1. `GET /users`: Retorna a lista de todos os usuários.
2. `GET /users/{id}`: Retorna os detalhes de um usuário específico.
3. `POST /users`: Adiciona um novo usuário.
4. `PUT /users/{id}`: Atualiza os dados de um usuário existente.
5. `DELETE /users/{id}`: Remove um usuário.