from flask import request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity # Importe get_jwt_identity
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import Unauthorized, Forbidden, HTTPException

import logging
import sys # Para printar no stderr durante depuração

jwt = JWTManager()

def configure_auth(app):
    jwt.init_app(app)

    @jwt.unauthorized_loader
    def unauthorized_response(error):
        print('SOCORRO')
        return jsonify({
            'message': "Autenticação inválida",
            'errors': f"Token de autorização não fornecido ou inválido. Detalhe: {error}",
            'code': 401 # Este 'code' é para o JSON no corpo da resposta
        }), 401 # <-- RETORNE o JSON e o CÓDIGO HTTP aqui

    @jwt.invalid_token_loader
    def invalid_token_response(callback):
        print("===== JWT LOADER: invalid_token_response EXECUTADO =====", file=sys.stderr)
        current_app.logger.error(f"JWT Invalid Token Loader triggered: {callback}")
        raise HTTPException(
            code=401,
            description="Token de autorização inválido.",
            response=jsonify({'message': "Autenticação inválida", 'errors': "Token de autorização inválido."}, code=401),
            
        )

    @jwt.expired_token_loader
    def expired_token_response(callback):
        print("===== JWT LOADER: expired_token_response EXECUTADO =====", file=sys.stderr)
        current_app.logger.error(f"JWT Expired Token Loader triggered: {callback}")
        raise HTTPException(
            description="Token de autorização expirado.",
            response=jsonify({'message': "Autenticação inválida", 'errors': "Token de autorização expirado."})
        )

    @jwt.revoked_token_loader
    def revoked_token_response(callback):
        print("===== JWT LOADER: revoked_token_response EXECUTADO =====", file=sys.stderr)
        current_app.logger.error(f"JWT Revoked Token Loader triggered: {callback}")
        raise HTTPException(
            description="Token de autorização revogado.",
            response=jsonify({'message': "Autenticação inválida", 'errors': "Token de autorização revogado."}),
            code=401
        )

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_response(jwt_header, jwt_payload):
        print("===== JWT LOADER: needs_fresh_token_response EXECUTADO =====", file=sys.stderr)
        current_app.logger.error("JWT Needs Fresh Token Loader triggered.")
        raise HTTPException(
            description="Token de autorização precisa ser 'fresh'.",
            response=jsonify({'message': "Autenticação inválida", 'errors': "Token de autorização precisa ser 'fresh'."}),
            code=401
        )

    # Rota de login
    @app.route('/login', methods=['POST'])
    def login():
        email = request.json.get('email', None)
        password = request.json.get('password', None)

        user = User.query.filter_by(email=email).first()
        if not user or password != 'password': # Lógica de senha simplificada para exemplo
            print("===== LOGIN: Credenciais Inválidas EXECUTADO =====", file=sys.stderr)
            raise HTTPException(
                description="Email ou senha inválidos",
                response=jsonify({'message': "Autenticação inválida", 'errors': "Email ou senha inválidos"}),
                code=401
            )

        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token)

    # Exemplo de rota Flask normal (não Smorest) com JWT
    @app.route('/protected-flask-route', methods=['GET'])
    @jwt_required()
    def protected_flask_route():
        current_user = get_jwt_identity()
        current_app.logger.info("Acesso à rota Flask protegida com sucesso.")
        return jsonify({"hello": "from protected Flask endpoint", "user": current_user}), 200