import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Modelos centralizados
from models import db, Usuario, Video, Pedido

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_super_segura_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plataforma.db'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# Inicializa o banco de dados
db.init_app(app)

with app.app_context():
    db.create_all()


# --- ROTA DA LOJA (HOME / LANDING PAGE) ---
@app.route('/')
def index():
    query = request.args.get('q', '')
    if query:
        videos = Video.query.filter(Video.titulo.ilike(f'%{query}%')).all()
    else:
        videos = Video.query.all()
    return render_template('index.html', videos=videos)


# --- CAPTURA DE LEADS (MODAL CHECKOUT) ---
@app.route('/processar_pedido', methods=['POST'])
def processar_pedido():
    pacote = request.form.get('pacote')
    nome = request.form.get('nome')
    email = request.form.get('email')
    whatsapp = request.form.get('whatsapp')

    novo_pedido = Pedido(
        pacote=pacote,
        nome_cliente=nome,
        email_cliente=email,
        whatsapp_cliente=whatsapp,
        status='Aguardando Pagamento'
    )

    try:
        db.session.add(novo_pedido)
        db.session.commit()
        flash(f'Pedido recebido! Entraremos em contato pelo WhatsApp ({whatsapp}).', 'success')
        return redirect(url_for('index'))

    except Exception as e:
        db.session.rollback()
        flash('Ocorreu um erro ao enviar seu pedido. Tente novamente.', 'danger')
        return redirect(url_for('index'))


# --- LOGIN (SOMENTE ADMINISTRADOR) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        user = Usuario.query.filter_by(email=email).first()
        
        # Apenas administradores conseguem autenticar
        if user and check_password_hash(user.senha, senha) and user.is_admin:
            session['user_id'] = user.id
            session['user_name'] = user.nome
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        
        flash('Acesso negado. Credenciais inválidas ou sem acesso de admin.', 'danger')
        
    return render_template('login.html')


# --- PAINEL ADMINISTRATIVO ---
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
        
    videos = Video.query.all()
    pedidos = Pedido.query.order_by(Pedido.id.desc()).all()
    
    return render_template('admin/dashboard.html', videos=videos, pedidos=pedidos)


# --- UPLOAD DE VÍDEOS PELO ADMIN ---
@app.route('/admin/videos/novo', methods=['POST'])
def adicionar_video():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
        
    titulo = request.form['titulo']
    descricao = request.form.get('descricao', '')
    preco = float(request.form.get('preco', 0))
    file = request.files.get('file')
    
    if file:
        filename = secure_filename(file.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        novo_video = Video(titulo=titulo, descricao=descricao, preco=preco, filename=filename)
        db.session.add(novo_video)
        db.session.commit()
        
        flash('Vídeo cadastrado com sucesso!', 'success')
        
    return redirect(url_for('admin_dashboard'))


# --- EXCLUIR VÍDEO DO PORTFÓLIO ---
@app.route('/excluir_video/<int:id>', methods=['POST'])
def excluir_video(id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    video = Video.query.get_or_404(id)
    caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
    
    if os.path.exists(caminho_arquivo):
        try:
            os.remove(caminho_arquivo)
        except Exception as e:
            print(f"Erro ao excluir arquivo físico: {e}")
    
    try:
        db.session.delete(video)
        db.session.commit()
        flash('Vídeo excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir do banco de dados.', 'danger')
        
    return redirect(url_for('admin_dashboard'))


# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)