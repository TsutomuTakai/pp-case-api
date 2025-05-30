from flask import jsonify, request, current_app
import sys
from models import db, User
from schemas import UserSchema, UserInputSchema, PaginatedUserSchema, UserQueryArgsSchema # Importe todos os schemas necessários
from flask_jwt_extended import jwt_required, get_jwt_identity # Importe jwt_required e get_jwt_identity
from flask_smorest import Blueprint, abort # Importe Blueprint e abort do Flask-Smorest
from flask.views import MethodView
from marshmallow import fields, validate # Importe do marshmallow diretamente se precisar de validadores

# Crie um Blueprint do Smorest
# O prefixo da URL aqui define o namespace da sua API (ex: /v1)
# doc_name e doc_version são para a documentação OpenAPI
blp_v1 = Blueprint(
    'api_v1', 'api_v1', url_prefix='/v1',
    description='Operações da API de Usuários (Versão 1)',
)

# --- Manipuladores de Erro Específicos do Smorest (Opcional, se precisar de formatação diferente) ---
# Você já tem manipuladores globais em app.py, mas pode adicionar específicos aqui.
# Exemplo para um erro de validação (BadRequest)
@blp_v1.errorhandler(400) # Smorest lida com 400s de validação automaticamente, mas pode ser customizado
def handle_smorest_bad_request(error):
    # Flask-Smorest geralmente formata erros de validação bem.
    # Você pode personalizar o corpo da resposta de erro aqui se quiser.
    current_app.logger.error(f"Smorest Bad Request: {error.messages}")
    return jsonify({
        'message': 'Dados de entrada inválidos',
        'errors': error.messages # `error.messages` contém os detalhes da validação
    }), 400

# --- Fim Manipuladores de Erro Específicos do Smorest ---


# --- RECURSO: Listagem e Criação de Usuários ---
@blp_v1.route('/users')
class UserList(MethodView): # Use MethodView
    @blp_v1.doc(description='Retorna a lista de todos os usuários com filtros e paginação.')
    @blp_v1.arguments(UserQueryArgsSchema, location='query') # Schema para query parameters
    @blp_v1.response(200, PaginatedUserSchema) # Schema para a resposta paginada
    @jwt_required() # Protegido por JWT
    def get(self, args):
        print("!!!!! DENTRO DO MÉTODO GET UserList !!!!!", file=sys.stderr) # Para depuração

        # Lógica de filtragem
        query = User.query
        if args.get('email'):
            query = query.filter(User.email.ilike(f"%{args['email']}%"))
        if args.get('name'):
            query = query.filter(User.name.ilike(f"%{args['name']}%"))

        # Lógica de paginação
        page = args.get('page', 1)
        per_page = args.get('per_page', 10)
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # Monta a resposta paginada
        return {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total,
            'items': pagination.items
        }

    @blp_v1.doc(description='Cria um novo usuário.')
    @blp_v1.arguments(UserInputSchema) # Schema para validação do corpo da requisição (JSON)
    @blp_v1.response(201, UserSchema, description="Usuário criado com sucesso")
    @jwt_required() # Protegido por JWT
    def post(self, new_user_data):
        print("!!!!! DENTRO DO MÉTODO POST UserList !!!!!", file=sys.stderr) # Para depuração
        if User.query.filter_by(email=new_user_data['email']).first():
            abort(409, message="Um usuário com este e-mail já existe.") # Use abort do Smorest
        user = User(**new_user_data)
        user.set_password(new_user_data['password']) # Hash da senha
        db.session.add(user)
        db.session.commit()
        return user # O Smorest serializa automaticamente com UserSchema (definido no @blp_v1.response)


# --- RECURSO: Detalhes, Atualização e Exclusão de Usuários ---
@blp_v1.route('/users/<int:user_id>')
class UserResource(MethodView): # Use MethodView
    @blp_v1.doc(description='Retorna os detalhes de um usuário específico.')
    @blp_v1.response(200, UserSchema)
    @blp_v1.alt_response(404, description="Usuário não encontrado") # Documenta um possível 404
    @jwt_required() # Protegido por JWT
    def get(self, user_id):
        print(f"!!!!! DENTRO DO MÉTODO GET UserResource para user_id: {user_id} !!!!!", file=sys.stderr) # Para depuração
        user = User.query.get_or_404(user_id, description="Usuário não encontrado.") # get_or_404 do SQLAlchemy
        return user

    @blp_v1.doc(description='Atualiza um usuário existente.')
    @blp_v1.arguments(UserInputSchema(partial=True)) # partial=True permite atualizações parciais
    @blp_v1.response(200, UserSchema, description="Usuário atualizado com sucesso")
    @blp_v1.alt_response(404, description="Usuário não encontrado")
    @jwt_required() # Protegido por JWT
    def put(self, new_user_data, user_id):
        print(f"!!!!! DENTRO DO MÉTODO PUT UserResource para user_id: {user_id} !!!!!", file=sys.stderr) # Para depuração
        user = User.query.get_or_404(user_id, description="Usuário não encontrado.")
        if 'email' in new_user_data and new_user_data['email'] != user.email:
            if User.query.filter_by(email=new_user_data['email']).first():
                abort(409, message="Um usuário com este e-mail já existe.")
        
        # Atualiza os campos do usuário
        for key, value in new_user_data.items():
            if key == 'password':
                user.set_password(value) # Hash da senha
            else:
                setattr(user, key, value)
        
        db.session.commit()
        return user # Smorest serializa automaticamente

    @blp_v1.doc(description='Exclui um usuário existente.')
    @blp_v1.response(204, description="Usuário excluído com sucesso") # 204 No Content
    @blp_v1.alt_response(404, description="Usuário não encontrado")
    @jwt_required() # Protegido por JWT
    def delete(self, user_id):
        print(f"!!!!! DENTRO DO MÉTODO DELETE UserResource para user_id: {user_id} !!!!!", file=sys.stderr) # Para depuração
        user = User.query.get_or_404(user_id, description="Usuário não encontrado.")
        db.session.delete(user)
        db.session.commit()
        return '', 204 # Retorna vazio com status 204


# --- Função para configurar as rotas Smorest no app ---
def configure_routes_smorest(api_instance):
    # Registre o blueprint no Smorest API instance
    api_instance.register_blueprint(blp_v1)
    # Não há necessidade de app.register_blueprint aqui, o Smorest faz isso
    # A URL para a documentação será /openapi ou /docs (dependendo da configuração do Smorest)
    # As rotas serão /v1/users, /v1/users/<id>, etc.