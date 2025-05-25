from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
from models import User
from werkzeug.security import generate_password_hash, check_password_hash

jwt = JWTManager()

def configure_auth(app):
    jwt.init_app(app)

    # Nota: Para simplificar, estamos adicionando um campo 'password_hash' ao User
    # Em um cenário real, você adicionaria isso ao seu modelo User e gerenciaria senhas.
    # Para este exemplo, vamos simular um usuário para login.
    # Em um projeto real, você teria um campo 'password_hash' no modelo User.

    @app.route('/login', methods=['POST'])
    def login():
        """
        Endpoint para login de usuário e obtenção de token JWT.
        Para fins de demonstração, aceita qualquer email e uma senha fixa 'password'.
        Em um ambiente de produção, você verificaria a senha hashada do banco de dados.
        """
        email = request.json.get('email', None)
        password = request.json.get('password', None)

        # Simulação de verificação de usuário e senha
        # Em produção, você buscaria o usuário no banco de dados e verificaria o hash da senha
        user = User.query.filter_by(email=email).first()
        if password != 'password': # Substitua 'password' pela verificação de hash real
            print(password)
            return jsonify({"msg": "Email ou senha inválidos"}), 401

        access_token = create_access_token(identity='password')
        
        return jsonify(access_token=access_token)

    @app.route('/protected', methods=['GET'])
    @jwt_required()
    def protected():
        """
        Endpoint de exemplo protegido por JWT.
        """
        return jsonify({"hello": "from protected endpoint"}), 200
