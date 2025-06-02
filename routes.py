import sys
from flask import jsonify, request, current_app
from flask.views import MethodView 
from models import db, User # Importe User para as operações de DB
from schemas import UserSchema, UserInputSchema, PaginatedUserSchema, UserQueryArgsSchema 
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint, abort 
from flask_limiter import Limiter 
from flask_caching import Cache 

limiter = Limiter(key_func=lambda: request.remote_addr) # key_func padrão
cache = Cache()

# Crie um Blueprint do Smorest
blp_v1 = Blueprint(
    'api_v1', __name__, url_prefix='/v1', # __name__ como segundo argumento para o Blueprint
    description='Operações da API de Usuários (Versão 1)'
)

@blp_v1.errorhandler(400) 
def handle_smorest_bad_request(error):
    current_app.logger.error(f"Smorest Bad Request: {error.messages}")
    return jsonify({
        'message': 'Dados de entrada inválidos',
        'errors': error.messages # `error.messages` contém os detalhes da validação
    }), 400

@blp_v1.errorhandler(409) 
def handle_smorest_conflict(error):
    current_app.logger.error(f"Smorest Conflict: {error}")
    return jsonify({
        'message': 'Um usuário com este e-mail já existe',
        'error': f"{error}"
    }), 409


# --- RECURSO: Listagem e Criação de Usuários ---
@blp_v1.route('/users')
class UserList(MethodView):
    @blp_v1.doc(description='Retorna a lista de todos os usuários com filtros e paginação.')
    @blp_v1.arguments(UserQueryArgsSchema, location='query') # Schema para query parameters
    @blp_v1.response(200, PaginatedUserSchema) # Schema para a resposta paginada
    @limiter.limit("10/minute")
    def get(self, args):
        query = User.query
        if args.get('email'):
            query = query.filter(User.email.ilike(f"%{args['email']}%"))
        if args.get('name'):
            query = query.filter(User.name.ilike(f"%{args['name']}%"))

        sort_by = args.get('sort_by', 'id')
        order = args.get('order', 'asc')
        if sort_by:
            if order == 'desc':
                query = query.order_by(getattr(User, sort_by).desc())
            else:
                query = query.order_by(getattr(User, sort_by).asc())

        page = args.get('page', 1)
        per_page = args.get('per_page', current_app.config.get('PER_PAGE', 10))
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total,
            'items': pagination.items # Usando 'items' do Smorest
        }

    @blp_v1.doc(description='Cria um novo usuário.')
    @blp_v1.arguments(UserInputSchema) 
    @blp_v1.response(201, UserSchema, description="Usuário criado com sucesso")
    @jwt_required() 
    def post(self, new_user_data): 
        current_user_id = get_jwt_identity()
        current_app.logger.info(f"Usuário {current_user_id} tentando adicionar um novo usuário.")

        if User.query.filter_by(email=new_user_data['email']).first():
            abort(409, {'message':"Um usuário com este e-mail já existe."}) # Use abort do Smorest

        user = User(name=new_user_data['name'], email=new_user_data['email'])
        user.set_password(new_user_data['password']) # Hash da senha usando bcrypt
        db.session.add(user)
        db.session.commit()
        return user 

# --- RECURSO: Detalhes, Atualização e Exclusão de Usuários ---
@blp_v1.route('/users/<int:user_id>')
class UserResource(MethodView): 
    @blp_v1.doc(description='Retorna os detalhes de um usuário específico.')
    @blp_v1.response(200, UserSchema)
    @blp_v1.alt_response(404, description="Usuário não encontrado") # Documenta um possível 404
    def get(self, user_id):
        user = User.query.get_or_404(user_id, description="Usuário não encontrado.")
        return user 

    @blp_v1.doc(description='Atualiza um usuário existente.')
    @blp_v1.arguments(UserInputSchema(partial=True)) # partial=True permite atualizações parciais
    @blp_v1.response(200, UserSchema, description="Usuário atualizado com sucesso")
    @blp_v1.alt_response(404, description="Usuário não encontrado")
    @jwt_required() # Protegido por JWT
    def put(self, update_data, user_id): 
        current_user_id = get_jwt_identity()
        current_app.logger.info(f"Usuário {current_user_id} tentando atualizar o usuário {user_id}.")

        user = User.query.get_or_404(user_id, description="Usuário não encontrado.")

        if 'email' in update_data and update_data['email'] != user.email:
            if User.query.filter(User.email == update_data['email'], User.id != user_id).first():
                abort(409, {'message':"Um usuário com este e-mail já existe."})

        for key, value in update_data.items():
            if key == 'password':
                user.set_password(value) # Hash da senha
            else:
                setattr(user, key, value)

        db.session.commit()
        return user 

    @blp_v1.doc(description='Exclui um usuário existente.')
    @blp_v1.response(204, description="Usuário excluído com sucesso") 
    @blp_v1.alt_response(404, description="Usuário não encontrado")
    @jwt_required() # Protegido por JWT
    def delete(self, user_id):
        current_user_id = get_jwt_identity()
        current_app.logger.info(f"Usuário {current_user_id} tentando deletar o usuário {user_id}.")

        user = User.query.get_or_404(user_id, description="Usuário não encontrado.")
        db.session.delete(user)
        db.session.commit()
        return '', 204

def configure_routes_smorest(api_instance):
    api_instance.register_blueprint(blp_v1)
