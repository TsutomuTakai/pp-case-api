# schemas.py
from flask_marshmallow import Marshmallow
from flask_marshmallow.sqla import SQLAlchemyAutoSchema # CORREÇÃO: Importar de .sqla
from models import User

ma = Marshmallow()

class UserSchema(SQLAlchemyAutoSchema): # Herda diretamente de SQLAlchemyAutoSchema
    class Meta:
        model = User
        load_instance = True # Permite carregar dados em instâncias do modelo
        include_fk = True # Inclui chaves estrangeiras se houver
        # fields = ("id", "name", "email") # Você pode especificar os campos explicitamente

user_schema = UserSchema()
users_schema = UserSchema(many=True)
