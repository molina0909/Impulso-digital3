from flask_sqlalchemy import SQLAlchemy

# Cria a instância do db para que as classes possam herdar de db.Model
db = SQLAlchemy()

# --- TABELA DE USUÁRIO (ADMIN) ---
class Usuario(db.Model):
    __tablename__ = 'usuario'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)


# --- TABELA DE VÍDEOS (PORTFÓLIO) ---
class Video(db.Model):
    __tablename__ = 'video'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Float, nullable=False)
    filename = db.Column(db.String(255), nullable=False)


# --- TABELA DE PEDIDOS / LEADS ---
class Pedido(db.Model):
    __tablename__ = 'pedido'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    pacote = db.Column(db.String(100), nullable=False)
    nome_cliente = db.Column(db.String(100), nullable=False)
    email_cliente = db.Column(db.String(120), nullable=False)
    whatsapp_cliente = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), default='Aguardando Pagamento')