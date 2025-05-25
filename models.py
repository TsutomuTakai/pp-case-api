# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.email}>'

    # O método to_dict() não é mais estritamente necessário com Marshmallow,
    # mas pode ser útil para depuração ou para casos específicos.
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }
