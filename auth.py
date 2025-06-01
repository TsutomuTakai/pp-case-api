import sys
from flask import request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity
from models import User 
from models import bcrypt_obj 

jwt = JWTManager()

def configure_auth(app):
    jwt.init_app(app)

    # Callback para carregar um objeto de usuário a partir do ID contido no token
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"] # onde sub é o padrão do JWT
        return User.query.filter_by(id=identity).one_or_none()

    # Callback para lidar com tokens não fornecidos ou inválidos
    @jwt.unauthorized_loader
    def unauthorized_response(callback_error):
        current_app.logger.warning(f"JWT Unauthorized: {callback_error}")
        return jsonify({
            'message': "Autenticação inválida",
            'errors': f"Token de autorização não fornecido ou inválido. Detalhe: {callback_error}",
            'code': 401
        }), 401

    # Callback para lidar com tokens expirados
    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_data):
        current_app.logger.warning(f"JWT Expired: Token de {jwt_data['sub']} expirou.")
        return jsonify({
            'message': "Autenticação inválida",
            'errors': "Seu token de autorização expirou.",
            'code': 401
        }), 401

    # Callback para lidar com tokens inválidos (assinatura, estrutura, etc.)
    @jwt.invalid_token_loader
    def invalid_token_response(callback_error):
        current_app.logger.warning(f"JWT Invalid Token: {callback_error}")
        return jsonify({
            'message': "Autenticação inválida",
            'errors': f"Seu token de autorização é inválido. Detalhe: {callback_error}",
            'code': 401
        }), 401


    # Rota de login
    @app.route('/login', methods=['POST'])
    def login():
        email = request.json.get('email', None)
        password = request.json.get('password', None)

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            current_app.logger.warning(f"Login falhou para: {email}")
            return jsonify({'message': "Autenticação inválida", 'errors': "Email ou senha inválidos"}), 401

        access_token = create_access_token(identity=user.id)
        current_app.logger.info(f"Login bem-sucedido para: {email}")
        return jsonify(access_token=access_token)
