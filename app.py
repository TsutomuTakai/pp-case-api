import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, request, current_app
from flask_smorest import Api 
from werkzeug.exceptions import HTTPException, NotFound, BadRequest, Unauthorized, TooManyRequests, Conflict, UnprocessableEntity
from models import db, migrate, bcrypt_obj, User
from schemas import ma 
from auth import configure_auth, jwt 
from routes import configure_routes_smorest, limiter, cache

def create_app(config_object='config.Config'):
    """Cria e configura o aplicativo Flask."""
    app = Flask(__name__)
    app.config.from_object(config_object)

    instance_path = os.path.join(app.root_path, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    # Configuração de Logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/flask_crud.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

    # Inicializa extensões Flask
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt_obj.init_app(app) 
    ma.init_app(app) 
    limiter.init_app(app)
    cache.init_app(app)
    configure_auth(app) # Configura JWT

    api = Api(app, spec_kwargs={"openapi_version": app.config["OPENAPI_VERSION"]})

    @app.errorhandler(NotFound) 
    def handle_not_found_error(e):
        """Captura erros 404."""
        current_app.logger.error(f"404 Not Found: {e.description}")
        return jsonify({'message': 'Recurso não encontrado', 'code': 404}), 404

    @app.errorhandler(BadRequest)
    def handle_bad_request_error(e):
        """Captura erros 400."""
        current_app.logger.error(f"400 Bad Request: {e.description}")
        errors_detail = e.messages if hasattr(e, 'messages') else e.description
        return jsonify({'message': 'Requisição inválida', 'errors': errors_detail, 'code': 400}), 400

    @app.errorhandler(Unauthorized) 
    def handle_unauthorized_error(e):
        """Captura erros 401."""
        current_app.logger.error(f"401 Unauthorized: {e.description}")
        if e.response:
            return e.response, e.code
        return jsonify({'message': 'Autenticação inválida', 'errors': e.description, 'code': 401}), 401
    
    @app.errorhandler(UnprocessableEntity) 
    def handle_smorest_bad_request_error(e):
        """Captura erros 422."""
        current_app.logger.error(f"422 Unprocessable Entity: {e.description}")
        errors_detail = e.messages if hasattr(e, 'messages') else e.description
        return jsonify({'message': 'Dados de entrada inválidos', 'errors': errors_detail, 'code': 422}), 422
    
    @app.errorhandler(TooManyRequests) 
    def handle_too_many_requests_error(e):
        """Captura erros 429."""
        current_app.logger.error(f"429 Too Many Requests: {e.description}")
        return jsonify({'message': 'Muitas requisições', 'errors': e.description, 'code': 429}), 429

    @app.errorhandler(Conflict) 
    def handle_conflict_error(e):
        """Captura erros 409."""
        current_app.logger.error(f"409 Conflict: {e.description}")
        return jsonify({'message': 'Conflito de recurso', 'errors': e.description, 'code': 409}), 409

    @app.errorhandler(HTTPException) 
    def handle_http_exception(e):
        """Captura erros HTTP."""
        current_app.logger.error(f"HTTP Exception caught: {e.code} - {e.description}", exc_info=True)
        if e.response:
            return e.response, e.code 
        return jsonify({
            'message': e.description if hasattr(e, 'description') else 'Um erro HTTP ocorreu',
            'code': e.code
        }), e.code

    @app.errorhandler(Exception) 
    def handle_generic_error(e):
        """Captura erros genéricos."""
        current_app.logger.exception(f"Erro interno do servidor: {e}") # Loga a exceção completa
        return jsonify({'message': 'Ocorreu um erro interno no servidor', 'error': 'Erro inesperado'}), 500


    # Registra os Blueprints do Flask-Smorest
    configure_routes_smorest(api)

    with app.app_context():
        print(app.config['SQLALCHEMY_DATABASE_URI'])
        db.create_all() # Cria as tabelas se não existirem
        # Adição usuário de teste 
        if not User.query.filter_by(email="test@example.com").first():
            test_user = User(name="Test User", email="test@example.com")
            test_user.set_password("password") # Definir uma senha para o usuário de teste
            db.session.add(test_user)
            db.session.commit()
            current_app.logger.info("Usuário de teste 'test@example.com' criado.")
        else:
            current_app.logger.info("Usuário de teste 'test@example.com' já existe.")

    return app

if __name__ == '__main__':
    """Execução do aplicativo Flask."""
    app = create_app()
