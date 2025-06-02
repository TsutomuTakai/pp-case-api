from flask_marshmallow import Marshmallow
from marshmallow import fields, validate
from models import User 
ma = Marshmallow()

# Schema para validação de entrada de usuário (criação/atualização)
class UserInputSchema(ma.Schema):
    email = fields.String(required=True, validate=validate.Email())
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=6)) # load_only: não será serializado na saída
    name = fields.String(required=True)

# Schema para saída de usuário (detalhes do usuário)
class UserSchema(ma.SQLAlchemyAutoSchema): # Use SQLAlchemyAutoSchema para gerar automaticamente campos do modelo
    class Meta:
        model = User
        load_instance = True 
        include_fk = True
        load_only = ('password_hash',)
        dump_only = ('id',)

# Schema para paginação de usuários (saída)
class PaginatedUserSchema(ma.Schema):
    page = fields.Integer(dump_only=True, metadata={"description": "Número da página"})
    per_page = fields.Integer(dump_only=True, metadata={"description": "Itens por página"})
    total_pages = fields.Integer(dump_only=True, metadata={"description": "Número total de páginas"})
    total_items = fields.Integer(dump_only=True, metadata={"description": "Total de itens"})
    items = fields.List(fields.Nested(UserSchema), dump_only=True,metadata={"description": "Itens da página"})

# Schema para filtros de usuário (entrada - query parameters)
class UserQueryArgsSchema(ma.Schema):
    email = fields.String(metadata={"description": "Filtrar por e-mail (busca parcial)"})
    name = fields.String(metadata={"description": "Filtrar por nome (busca parcial)"})
    page = fields.Integer(load_default=1, validate=validate.Range(min=1), metadata={"description": "Número da página"})
    per_page = fields.Integer(load_default=10, validate=validate.Range(min=1, max=100), metadata={"description": "Itens por página"})