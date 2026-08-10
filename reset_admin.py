from app import app
from models import db, Usuario
from werkzeug.security import generate_password_hash

with app.app_context():
    # Procura se o admin já existe e apaga para recriar limpo
    admin_antigo = Usuario.query.filter_by(email='admin@loja.com').first()
    if admin_antigo:
        db.session.delete(admin_antigo)
        db.session.commit()
        print("🗑️ Admin antigo removido.")

    # Cria o novo admin zerado
    novo_admin = Usuario(
        nome='Administrador',
        email='admin@loja.com',
        senha=generate_password_hash('123456'),
        is_admin=True
    )
    db.session.add(novo_admin)
    db.session.commit()
    
    print("✅ NOVO ADMIN CRIADO COM SUCESSO!")
    print("📧 Email: admin@loja.com")
    print("🔑 Senha: 123456")
