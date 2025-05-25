from flask import Flask, jsonify, request # Adicione 'request' aqui
from models import db
from schemas import ma
# from routes import configure_routes, api, limiter, cache # Pode importar aqui ou dentro de create_app

from auth import configure_auth, jwt
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import os

# Importe werkzeug.exceptions para erros mais específicos
from werkzeug.exceptions import HTTPException, NotFound, BadRequest, Conflict

def create_app(config_object='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_object)

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
        app.logger.info('Flask CRUD startup')

    # --- REGISTRO DOS MANIPULADORES DE ERRO GLOBAIS NO APP ---
    @app.errorhandler(NotFound) # Para 404s, incluindo os de get_or_404
    def handle_not_found_error(e):
        app.logger.warning(f"404 Not Found: {request.url}") # Log a URL não encontrada
        return jsonify({'message': 'Recurso não encontrado', 'error': str(e)}), 404

    @app.errorhandler(BadRequest) # Para 400s
    def handle_bad_request_error(e):
        errors_detail = e.data.get('errors') if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)
        app.logger.error(f"400 Bad Request: {errors_detail}")
        return jsonify({'message': 'Requisição inválida', 'errors': errors_detail}), 400

    @app.errorhandler(Conflict) # Para 409s
    def handle_conflict_error(e):
        errors_detail = e.data.get('errors') if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)
        app.logger.error(f"409 Conflict: {errors_detail}")
        return jsonify({'message': 'Conflito de dados', 'errors': errors_detail}), 409

    @app.errorhandler(HTTPException) # Para outros erros HTTP (e.g., 401, 403, 405)
    def handle_http_exception(e):
        app.logger.error(f"HTTP Exception {e.code}: {e.description}")
        return jsonify({'message': e.description, 'code': e.code}), e.code

    @app.errorhandler(Exception) # Manipulador genérico para qualquer outra exceção não tratada
    def handle_generic_error(e):
        app.logger.exception(f"Erro interno do servidor: {e}") # Loga a exceção completa com traceback
        return jsonify({'message': 'Ocorreu um erro interno no servidor', 'error': 'Erro inesperado'}), 500
    # --- FIM DOS MANIPULADORES DE ERRO GLOBAIS ---

    db.init_app(app)
    ma.init_app(app)
    configure_auth(app) # Configura JWT
    migrate = Migrate(app, db) # Inicializa Flask-Migrate

    # Importe e configure as rotas aqui, após o app ter seus errorhandlers
    from routes import configure_routes, limiter, cache # api já é importado e configurado dentro de configure_routes
    configure_routes(app) # Configura as rotas e a API Flask-RESTX, e inicializa limiter e cache

    with app.app_context():
        # db.create_all() é para testes com banco de dados em memória ou para criar
        # um banco inicial se não usar migrações. Para migrações, 'flask db upgrade'.
        if app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:':
            db.create_all()

    return app

if __name__ == '__main__':
    # Para rodar em desenvolvimento: flask run
    # Para produção (Gunicorn): gunicorn --bind 0.0.0.0:5000 "app:create_app()"
    app = create_app()
    print("Para rodar em desenvolvimento, use 'flask run'. Para produção, use gunicorn ou podman-compose.")
