from flask import Flask, jsonify, request, current_app
from models import db
from schemas import ma
from auth import configure_auth, jwt
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import os
from werkzeug.exceptions import HTTPException, NotFound, BadRequest, Conflict, Unauthorized, TooManyRequests, InternalServerError
import sys

# Importar o Smorest API e Blueprint
from flask_smorest import Api, Blueprint

def create_app(config_object='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_object)
    print(f"Config object: {app.config.get('SQLALCHEMY_DATABASE_URI')}", file=sys.stderr)


    configure_auth(app) # Configura JWT

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

    # --- INICIALIZAÇÃO DO SMOREST ---
    # Instanciar o Smorest API
    app.config["API_TITLE"] = "USER TEST REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config[
        "OPENAPI_SWAGGER_UI_URL"
    ] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config['API_SPEC_OPTIONS'] = {'security': [{"bearerAuth": []}], 'components': {
            "securitySchemes":
                {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
        }}
    
    # --- FIM INICIALIZAÇÃO DO SMOREST ---

    # --- MANIPULADORES DE ERRO GLOBAIS (mantidos no app.py) ---
    @app.errorhandler(NotFound)
    def handle_not_found_error(e):
        app.logger.warning(f"404 Not Found: {request.url}")
        return jsonify({'message': 'Recurso não encontrado', 'error': str(e)}), 404

    @app.errorhandler(BadRequest)
    def handle_bad_request_error(e):
        # Flask-Smorest já tem um tratamento robusto para BadRequest (erros de validação)
        # Este handler pegaria Bads Requests que não vêm do Smorest
        errors_detail = e.data.get('errors') if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)
        app.logger.error(f"400 Bad Request: {errors_detail}")
        return jsonify({'message': 'Requisição inválida', 'errors': errors_detail}), 400

    @app.errorhandler(TooManyRequests)
    def handle_too_many_requests_error(e):
        errors_detail = e.description if hasattr(e, 'description') else str(e)
        app.logger.error(f"429 Too Many Requests: {errors_detail}")
        return jsonify({'message': 'Limite de solicitações excedido', 'errors': errors_detail}), 429

    @app.errorhandler(Conflict)
    def handle_conflict_error(e):
        errors_detail = e.data.get('errors') if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)
        app.logger.error(f"409 Conflict: {errors_detail}")
        return jsonify({'message': 'Conflito de dados', 'errors': errors_detail}), 409

    @app.errorhandler(Unauthorized)
    def handle_unauthorized_error(e):
        print(f"\n--- DEBUG FLUXO DE ERRO: handle_unauthorized_error CALLED ---", file=sys.stderr)
        print(f"DEBUG FLUXO DE ERRO: Tipo da exceção: {type(e).__name__}, Descrição: {e.description}", file=sys.stderr)
        print(f"DEBUG FLUXO DE ERRO: 'e.response' existe? {e.response is not None}", file=sys.stderr)
        if e.response:
            print(f"DEBUG FLUXO DE ERRO: Retornando resposta pré-construída do handler Unauthorized.", file=sys.stderr)
            return e.response, 401 # ou e.code
        print(f"DEBUG FLUXO DE ERRO: Construindo nova resposta no handler Unauthorized.", file=sys.stderr)
        return jsonify({'message': 'Autenticação inválida', 'errors': e.description}), 401


    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        # Mantenha o logger para registro
        current_app.logger.error(f"HTTP Exception caught: {e.code} - {e.description}", exc_info=True)
        print(f"\n--- DEBUG FLUXO DE ERRO: handle_http_exception CALLED ---", file=sys.stderr)
        print(f"DEBUG FLUXO DE ERRO: Tipo da exceção: {type(e).__name__}, Código: {e.code}, Descrição: {e.description}", file=sys.stderr)
        print(f"DEBUG FLUXO DE ERRO: 'e.response' existe? {e.response is not None}", file=sys.stderr)

        if e.response:
            print(f"DEBUG FLUXO DE ERRO: Retornando resposta pré-construída do handler HTTPException. Status: {e.response.status_code}", file=sys.stderr)
            return e.response, e.code

        print(f"DEBUG FLUXO DE ERRO: Construindo nova resposta JSON no handler HTTPException genérico.", file=sys.stderr)
        return jsonify({
            'message': e.description if hasattr(e, 'description') else 'Um erro HTTP ocorreu',
            'code': e.code
        }), e.code

    @app.errorhandler(Exception)
    def handle_generic_error(e):
        current_app.logger.exception(f"--- DEBUG FLUXO DE ERRO: handle_generic_error CALLED para: {type(e).__name__} ---", exc_info=True)
        print(f"\n--- DEBUG FLUXO DE ERRO: handle_generic_error CALLED ---", file=sys.stderr)
        print(f"DEBUG FLUXO DE ERRO: Tipo da exceção: {type(e).__name__}, Erro: {e}", file=sys.stderr)
        return jsonify({'message': 'Ocorreu um erro interno no servidor', 'error': 'Erro inesperado'}), 500
        # --- FIM MANIPULADORES DE ERRO GLOBAIS ---


    

    # --- REGISTRO DOS BLUEPRINTS DO SMOREST ---
    # Importar e registrar os blueprints do Smorest
    from routes import configure_routes_smorest
    api = Api(app) # Inicializa o Smorest com o app
    db.init_app(app)
    ma.init_app(app)
    migrate = Migrate(app, db)
    configure_routes_smorest(api) # Passamos a instância 'api' para configurar as rotas
    print("\n--- ROTAS REGISTRADAS NO FLASK ---", file=sys.stderr)
    for rule in app.url_map.iter_rules():
        print(f"Rule: {rule.endpoint} | Path: {rule.rule} | Methods: {rule.methods}", file=sys.stderr)
    print("----------------------------------\n", file=sys.stderr)
    # --- FIM REGISTRO DOS BLUEPRINTS DO SMOREST ---

    with app.app_context():
        if app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:':
            db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    print("Para rodar em desenvolvimento, use 'flask run'. Para produção, use gunicorn ou podman-compose.")