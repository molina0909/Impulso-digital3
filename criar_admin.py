from app import app
from models import db, Usuario
from werkzeug.security import generate_password_hash

with app.app_context():
    # Verifica se já existe um email de admin
    admin_existente = Usuario.query.filter_by(email='admin@loja.com').first()
    
    if not admin_existente:
        senha_criptografada = generate_password_hash('123456')
        novo_admin = Usuario(
            nome='Administrador', 
            email='admin@loja.com', 
            senha=senha_criptografada, 
            is_admin=True
        )
        db.session.add(novo_admin)
        db.session.commit()
        print("✅ Administrador criado com sucesso!")
        print("📧 Email: admin@loja.com")
        print("🔑 Senha: 123456")
    else:
        print("⚠️ O usuário administrador já existe no banco de dados.")