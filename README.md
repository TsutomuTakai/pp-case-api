# API de Usuários - Teste
Repositório para etapa de avaliação

# Proposta
Seguir o guia **[proposto](doc/prova.md)**

# Para testar

1. Crie um ambiente virtual e instale as dependencias `pip install -r requirements.txt`

2. A aplicação funciona decentemente dando um simples `flask run`
    1. Você também pode construir a imagem Dockerfile

4. Após inicializar a aplicação do jeito que preferir recupere seu token de acesso
>  curl -X POST -H "Content-Type: application/json" -d "{\"email\": \"test@example.com\", \"password\": \"password\"}" http://localhost:5000/login

4. Uma interface completa do swagger-iu está disponível em http://localhost:5000/docs

5. Todos os testes unitários estão configurados e funcionais, basta executar o `pytest` no diretório raíz do repositório

6. De qualquer maneira que for inicializada a aplicação já existem dados populados na instancia do SQLite.

7. Sintam-se a vontade para testar e quebrar esta aplicação!

#  Visão Geral da Aplicação
1. **Flask**: pré-requisito da proposta, framework leve simples e com amplo suporte da comunidade desenvolvedora.
2. **SQLite**: pré-requisito da proposta, mini engine de SQL para aplicações de pequeno porte com poucos requisitos de memória.
3. **SQLAlchemy**: utilizado como ORM (Object-Relationa Mapper) para simplificar a interação com o banco de dados
4. **Marshmallow**: biblioteca utilizada para validação de dados além de lidar com a serialização de dados.
5. **Flask-Smorest**: framework para utilização em API's REST que concilia as funcionalidades do Flask e marshmallow, possibilita a geração de documentação, é agnóstico a banco de dados além de possuir um ciclo de desenvolvimento ativo
6. **Flask-JWT-Extended**: para criar um sistema simples de autenticação baseado em JWT.
7. **Flask-Migrate**: auxilia no versionamento de schemas do banco de dados
8. **Flask-Limiter**: protege a api contra ataques e sobrecargas de uso limitando a quantidade de acessos dentro de um período de tempo
9. **Flask-Caching**: otimiza a performance do serviço guardando em cache requisições frequentes, assim diminuindo os acessos ao banco de dados

## Estrutura do Código:
A estrutura do projeto foi pensada para que cada arquivo tenha uma responsabilidade bem definida, tornando o uso mais intuitivo e facilitando a manutenção da aplicação.

- `app.py`: Este é o ponto central da aplicação. Nele, a instância do Flask é criada, as rotas são carregadas e todas as extensões utilizadas pelo sistema são inicializadas.

- `models.py`: Responsável pela criação das classes que interagem diretamente com o banco de dados.

- `schemas.py`: Utiliza o Marshmallow para definir as estruturas de dados esperadas tanto na entrada quanto na saída das requisições da API.

- `routes.py`: Contém a definição de todos os endpoints da API. É configurado com o Flask-Smorest, o que permite a geração automática da documentação.

- `auth.py`: Um módulo dedicado à configuração do processo de autenticação. Embora esteja incluído aqui para fins de demonstração, em contextos de produção maiores, é recomendado que a autenticação seja gerenciada por um serviço à parte.

- `config.py`: Este arquivo centraliza todas as configurações da aplicação. Ele pode ser ajustado para diferenciar e gerenciar ambientes distintos, como desenvolvimento, homologação e produção.

## Melhorias Implementadas
Diversas melhorias foram aplicadas para tornar o projeto mais robusto, seguro e eficiente.

### Validação de Dados Robusta (com Marshmallow):

**Por que**: Assegura a integridade e consistência dos dados que entram e saem da API, evitando erros de aplicação, vulnerabilidades (como injeção de dados maliciosos) e melhorando a qualidade da informação.

**Como**: Usa schemas definidos em `schemas.py` com `marshmallow.fields` e validate para especificar tipos, formatos e regras de negócio para cada campo. O *Flask-Smorest* se integra com `@blp.arguments` para validar automaticamente os dados de entrada e `@blp.response` para serializar a saída.

### Tratamento de Erros Global e Personalizado:

**Por que**: Oferece uma experiência consistente e amigável para o usuário da API, retornando respostas de erro padronizadas em formato JSON com mensagens claras e códigos de status HTTP apropriados, em vez de erros genéricos do servidor. Facilita a depuração para os consumidores da API.

**Como**: Implementado em `app.py` com decoradores `@app.errorhandler()` para capturar exceções HTTP comuns (ex: `NotFound`, `BadRequest`, `Conflict`, `Unauthorized`, `TooManyRequests`) e um handler genérico para `HTTPException` e `Exception`. Os loaders do *Flask-JWT-Extended* em `auth.py` agora retornam diretamente respostas JSON para erros de autenticação, garantindo a consistência.

### Paginação, Filtragem e Ordenação:

**Por que**: Essencial para APIs que lidam com muitos dados. Melhora a performance (reduzindo a carga de dados transferidos e processados) e a usabilidade para o cliente, que pode buscar informações específicas de forma eficiente.

**Como**: Parâmetros de query (`page`, `per_page`, `email`, `name`, `sort_by`, `order`) são definidos e validados via `UserQueryArgsSchema` em `schemas.py` e `@blp.arguments` em `routes.py`. A lógica de consulta (`db.session.paginate()`, `.filter()`, `.order_by()`) é aplicada no método `GET` do `UserList`.

### Documentação da API (com Swagger/OpenAPI via Flask-Smorest):

**Por que**: Torna a API auto-descritiva e fácil de usar por outros desenvolvedores. A documentação interativa (Swagger UI) serve como um contrato claro entre a API e seus consumidores, diminuindo a curva de aprendizado e os erros de integração.

**Como**: O Flask-Smorest integra-se com `apispec` e `swagger-ui-bundle`. As descrições e schemas são automaticamente inferidos dos decoradores (`@blp.doc`, `@blp.arguments`, `@blp.response`) e dos schemas Marshmallow. A documentação é acessível em `/docs` e a especificação OpenAPI em `/openapi.json`.

### Autenticação (JWT - JSON Web Tokens):

**Por que**: Protege os endpoints da API, assegurando que apenas usuários autenticados e autorizados acessem recursos sensíveis ou modifiquem dados. Oferece um método seguro e escalável de verificação de identidade.

**Como**: Utiliza Flask-JWT-Extended para gerar e validar tokens JWT. O endpoint `/login` em `auth.py` emite tokens. O decorador `@jwt_required()` protege as rotas em `routes.py`, e os "loaders" em `auth.py` (como `unauthorized_loader`) fornecem respostas padronizadas para falhas de autenticação. O Flask-Bcrypt é usado para armazenar senhas de forma segura (hashing).

### Containerização (com Podman):

**Por que**: Garante um ambiente de execução consistente e portátil para a aplicação. Acaba com o "funciona na minha máquina", facilita o desenvolvimento em equipe e a implantação em diferentes ambientes (desenvolvimento, staging, produção). O Podman oferece uma alternativa segura ao Docker, sem a necessidade de um daemon root.

**Como**: Um `Dockerfile` define os passos para construir a imagem da aplicação (instalação de Python, dependências, cópia de código). O `compose.yaml` (usado com `podman-compose`) orquestra a execução da aplicação web e de um volume para o banco de dados, facilitando o gerenciamento de múltiplos serviços.

### Gerenciamento de Migrações de Banco de Dados (com Flask-Migrate):

**Por que**: Permite evoluir o esquema do banco de dados de forma controlada e segura à medida que o modelo de dados da aplicação muda (ex: adicionar novas colunas, alterar tipos de dados), sem perder dados existentes.

**Como**: Integrado com Flask-SQLAlchemy, permite gerar scripts de migração automaticamente (`flask db migrate`) e aplicá-los (`flask db upgrade`) ou revertê-los (`flask db downgrade`).

### Logging Adequado:

**Por que**: É essencial para monitorar o comportamento da aplicação, depurar problemas em desenvolvimento e identificar falhas em produção. Fornece visibilidade sobre o fluxo de requisições, erros e eventos importantes.

**Como**: Utiliza o módulo logging do Python, configurado em `app.py` para registrar mensagens em arquivos (`logs/flask_crud.log`) e no console. Mensagens de diferentes níveis (INFO, WARNING, ERROR, DEBUG) são usadas para granularidade.

### API Versioning:

**Por que**: Permite introduzir mudanças significativas na API sem quebrar a compatibilidade com clientes existentes. Clientes mais antigos podem continuar usando a versão anterior (ex: `/v1/users`), enquanto novos clientes podem migrar para a nova versão (ex: `/v2/users`) quando estiverem prontos.

**Como**: O Flask-Smorest facilita o versionamento através de `Blueprints` com prefixos de URL (`url_prefix='/v1'`). Isso isola as rotas de diferentes versões, tornando a gestão da compatibilidade retroativa mais simples.

### Rate Limiting (com Flask-Limiter):

**Por que**: Protege a API contra abusos, ataques de força bruta e sobrecarga de servidor, limitando o número de requisições que um cliente (identificado pelo IP) pode fazer em um determinado período.

**Como**: Utiliza Flask-Limiter. Configurado em `app.py` e `routes.py`, permite aplicar limites globais (`LIMITER_DEFAULT_LIMIT`) ou específicos por endpoint (`@limiter.limit("X per Y")`).

### Caching (com Flask-Caching):

**Por que**: Melhora a performance da API e reduz a carga sobre o banco de dados e outros recursos, armazenando em memória (ou outro backend como Redis) os resultados de requisições frequentes.

**Como**: Utiliza Flask-Caching. Configurado em `app.py`, permite cachear as respostas de endpoints `GET` com o decorador `@cache.cached(timeout=X)`. É crucial invalidar o cache (`cache.clear()`) em operações de escrita (POST, PUT, DELETE) para garantir que os dados retornados estejam sempre atualizados.

## Endpoints:
1. `GET /users`: Retorna a lista de todos os usuários.
2. `GET /users/{id}`: Retorna os detalhes de um usuário específico.
3. `POST /users`: Adiciona um novo usuário.
4. `PUT /users/{id}`: Atualiza os dados de um usuário existente.
5. `DELETE /users/{id}`: Remove um usuário.