# routes.py
from flask import request, jsonify, current_app
from flask_restx import Api, Resource, fields, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User
from schemas import user_schema, users_schema
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

# IMPORTAR AS EXCEÇÕES DO WERKZEUG AQUI
from werkzeug.exceptions import NotFound, BadRequest, Conflict, InternalServerError, HTTPException

authorizations = {
    'jwt': { # Este é o nome que você usará para referenciar este esquema de segurança
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Por favor, insira o token JWT com 'Bearer ' no início (ex: Bearer <token>)"
    }
}

api = Api(
    version='1.0',
    title='API de Gerenciamento de Usuários',
    description='Uma API CRUD simples para gerenciar usuários.',
    doc='/swagger-ui',
    security='jwt', # Define 'jwt' como o esquema de segurança padrão para toda a API
    authorizations=authorizations # Adiciona as definições de autorização
)
limiter = Limiter(
    key_func=get_remote_address,
    # default_limits e storage_uri serão configurados via app.config['LIMITER_DEFAULT_LIMIT']
)

cache = Cache()

# Modelo para documentação Swagger
user_model = api.model('User', {
    'id': fields.Integer(readOnly=True, description='O identificador único do usuário'),
    'name': fields.String(required=True, description='O nome do usuário'),
    'email': fields.String(required=True, description='O endereço de email do usuário'),
})

paginated_user_model = api.model('PaginatedUserList', {
    'users': fields.List(fields.Nested(user_model), description='Lista de usuários'),
    'total_users': fields.Integer(description='Número total de usuários'),
    'total_pages': fields.Integer(description='Número total de páginas'),
    'current_page': fields.Integer(description='Página atual'),
    'per_page': fields.Integer(description='Usuários por página'),
    'has_next': fields.Boolean(description='Se existe uma próxima página'),
    'has_prev': fields.Boolean(description='Se existe uma página anterior'),
    'next_page': fields.Integer(description='Número da próxima página (nulo se não houver)'),
    'prev_page': fields.Integer(description='Número da página anterior (nulo se não houver)')
})

user_input_model = api.model('UserInput', {
    'name': fields.String(required=True, description='O nome do usuário'),
    'email': fields.String(required=True, description='O endereço de email do usuário'),
})

def configure_routes(app):
    api.init_app(app)
    limiter.init_app(app) # Inicializa o limiter com a instância do app
    cache.init_app(app)   # Inicializa o cache com a instância do app

    # --- MANIPULADORES DE ERRO ESPECÍFICOS DA API (Flask-RESTX) ---
    # Estes são para exceções que o Flask-RESTX (ou Flask-SQLAlchemy) pode levantar
    # no contexto da API, como api.abort().
    @api.errorhandler(NotFound) # Passa a CLASSE NotFound
    def api_not_found_error(error):
        return {'message': 'Recurso não encontrado na API'}, 404

    @api.errorhandler(BadRequest) # Passa a CLASSE BadRequest
    def api_bad_request_error(error):
        errors_detail = error.data.get('errors') if hasattr(error, 'data') and error.data else str(error)
        return {'message': 'Requisição inválida na API', 'errors': errors_detail}, 400

    @api.errorhandler(Conflict) # Passa a CLASSE Conflict
    def api_conflict_error(error):
        errors_detail = error.data.get('errors') if hasattr(error, 'data') and error.data else str(error)
        return {'message': 'Conflito de dados na API', 'errors': errors_detail}, 409

    @api.errorhandler(Exception) # Captura qualquer outra exceção não tratada pela API
    def api_default_error_handler(error):
        current_app.logger.exception(f"Erro interno do servidor na API: {error}") # Loga a exceção completa
        return {'message': 'Ocorreu um erro interno no servidor na API'}, 500
    # --- FIM DOS MANIPULADORES DE ERRO DA API ---

    # Namespace para a versão 1 da API
    ns_v1 = api.namespace('v1', description='Operações de usuários')

    # Parser para paginação, filtragem e ordenação - MOVIDO PARA DENTRO DA FUNÇÃO
    parser = reqparse.RequestParser()
    parser.add_argument('page', type=int, help='Número da página', default=1)
    # Acessa app.config['PER_PAGE'] APÓS o app estar configurado
    parser.add_argument('per_page', type=int, help='Itens por página', default=app.config['PER_PAGE'])
    parser.add_argument('name', type=str, help='Filtrar por nome (substring)', location='args')
    parser.add_argument('email', type=str, help='Filtrar por email (substring)', location='args')
    parser.add_argument('sort_by', type=str, help='Campo para ordenação (name, email)', choices=('name', 'email'), location='args')
    parser.add_argument('order', type=str, help='Ordem (asc, desc)', choices=('asc', 'desc'), default='asc', location='args')

    @ns_v1.route('/users/')
    class UserList(Resource):
        @api.doc('listar_usuarios')
        @api.expect(parser)
        @ns_v1.marshal_list_with(paginated_user_model)
        @limiter.limit("10 per minute") # Limite específico para este endpoint
        @cache.cached(timeout=60, query_string=True) # Cacheia a resposta baseada na query string
        def get(self):
            """Retorna a lista de todos os usuários com paginação, filtragem e ordenação."""
            args = parser.parse_args()
            page = args['page']
            per_page = args['per_page']
            name_filter = args['name']
            email_filter = args['email']
            sort_by = args['sort_by']
            order = args['order']

            query = User.query

            if name_filter:
                query = query.filter(User.name.ilike(f'%{name_filter}%'))
            if email_filter:
                query = query.filter(User.email.ilike(f'%{email_filter}%'))

            if sort_by:
                if order == 'desc':
                    query = query.order_by(getattr(User, sort_by).desc())
                else:
                    query = query.order_by(getattr(User, sort_by).asc())

            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            users_data = users_schema.dump(pagination.items)

            # Retorne um dicionário Python que corresponda exatamente à estrutura do paginated_user_model.
            # O @ns_v1.marshal_with(paginated_user_model) cuidará de convertê-lo em JSON.
            return {
                'users': users_data, # Aqui você passa a lista de dicionários já serializada pelo Marshmallow
                'total_users': pagination.total,
                'total_pages': pagination.pages,
                'current_page': pagination.page,
                'per_page': pagination.per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_page': pagination.next_num,
                'prev_page': pagination.prev_num
            }

        @api.doc('criar_usuario')
        @api.expect(user_input_model)
        @ns_v1.marshal_with(user_model, code=201)
        @jwt_required()
        @limiter.limit("5 per minute") # Limite para criação de usuários
        def post(self):
            """Adiciona um novo usuário."""
            current_user_id = get_jwt_identity() # Obtém o ID do usuário logado
            current_app.logger.info(f"Usuário {current_user_id} tentando adicionar um novo usuário.")

            data = api.payload # Flask-RESTX já faz o parse do JSON

            # Validação de email duplicado
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                api.abort(409, "Email já cadastrado") # Lança um erro 409 com mensagem

            new_user = User(name=data['name'], email=data['email'])
            db.session.add(new_user)
            db.session.commit()
            cache.clear() # Limpa o cache após uma alteração nos dados
            return new_user, 201

    @ns_v1.route('/users/<int:user_id>')
    @api.param('user_id', 'O identificador do usuário')
    class UserResource(Resource):
        @api.doc('obter_usuario')
        @ns_v1.marshal_with(user_model)
        @limiter.limit("20 per minute") # Limite para recuperação de um usuário específico
        @cache.cached(timeout=60) # Cacheia a resposta por 60 segundos
        def get(self, user_id):
            """Retorna os detalhes de um usuário específico."""
            user = User.query.get_or_404(user_id, description='Usuário não encontrado')
            return user_schema.dump(user)

        @api.doc('atualizar_usuario')
        @api.expect(user_input_model)
        @ns_v1.marshal_with(user_model)
        @jwt_required() # Protege este endpoint com JWT
        @limiter.limit("5 per minute") # Limite para atualização de usuários
        def put(self, user_id):
            """Atualiza os dados de um usuário existente."""
            current_user_id = get_jwt_identity()
            current_app.logger.info(f"Usuário {current_user_id} tentando atualizar o usuário {user_id}.")

            user = User.query.get_or_404(user_id, description='Usuário não encontrado')
            data = api.payload

            if 'name' in data:
                user.name = data['name']
            if 'email' in data:
                # Validação de email duplicado para outros usuários
                existing_user = User.query.filter(User.email == data['email'], User.id != user_id).first()
                if existing_user:
                    api.abort(409, "Email já cadastrado para outro usuário")
                user.email = data['email']

            db.session.commit()
            cache.clear() # Limpa o cache após uma alteração nos dados
            return user_schema.dump(user)

        @api.doc('deletar_usuario')
        @api.response(204, 'Usuário deletado com sucesso')
        @jwt_required() # Protege este endpoint com JWT
        @limiter.limit("2 per minute") # Limite para deleção de usuários
        def delete(self, user_id):
            """Remove um usuário."""
            current_user_id = get_jwt_identity()
            current_app.logger.info(f"Usuário {current_user_id} tentando deletar o usuário {user_id}.")

            user = User.query.get_or_404(user_id, description='Usuário não encontrado')
            db.session.delete(user)
            db.session.commit()
            cache.clear() # Limpa o cache após uma alteração nos dados
            return '', 204

    @api.route('/protected')
    class ProtectedResource(Resource):
        @jwt_required()
        def get(self):
            current_user = get_jwt_identity()
            return jsonify({"hello": "from protected endpoint", "user": current_user})
