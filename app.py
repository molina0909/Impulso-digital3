import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

# =========================================================
# MODELOS
# =========================================================

from models import db, Usuario, Video, Pedido


# =========================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# =========================================================

app = Flask(__name__)

app.config['SECRET_KEY'] = 'sua_chave_secreta_super_segura_aqui'

# ---------------------------------------------------------
# BANCO SQLITE
# ---------------------------------------------------------
# O banco ficará na raiz do projeto:
# plataforma.db
# ---------------------------------------------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_PATH = os.path.join(BASE_DIR, 'plataforma.db')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    'sqlite:///' + DATABASE_PATH
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# ---------------------------------------------------------
# UPLOADS
# ---------------------------------------------------------

app.config['UPLOAD_FOLDER'] = os.path.join(
    BASE_DIR,
    'static',
    'uploads'
)


# Garante que a pasta de uploads exista
os.makedirs(
    app.config['UPLOAD_FOLDER'],
    exist_ok=True
)


# =========================================================
# INICIALIZAÇÃO DO BANCO
# =========================================================

db.init_app(app)


# =========================================================
# CRIAÇÃO / ATUALIZAÇÃO DO ADMINISTRADOR
# =========================================================

with app.app_context():

    # Cria as tabelas caso ainda não existam
    db.create_all()

    # -----------------------------------------------------
    # ADMIN PADRÃO
    # -----------------------------------------------------

    ADMIN_EMAIL = 'admin@loja.com'
    ADMIN_SENHA = '123456'

    admin_existente = Usuario.query.filter_by(
        email=ADMIN_EMAIL
    ).first()

    if not admin_existente:

        senha_criptografada = generate_password_hash(
            ADMIN_SENHA
        )

        novo_admin = Usuario(
            nome='Administrador',
            email=ADMIN_EMAIL,
            senha=senha_criptografada,
            is_admin=True
        )

        db.session.add(novo_admin)
        db.session.commit()

        print('==========================================')
        print(' ADMINISTRADOR CRIADO')
        print('==========================================')
        print(f' Email: {ADMIN_EMAIL}')
        print(f' Senha: {ADMIN_SENHA}')
        print('==========================================')

    else:

        # Garante que o usuário continue sendo administrador
        admin_existente.is_admin = True

        # Atualiza a senha para garantir que
        # 123456 funcione
        admin_existente.senha = generate_password_hash(
            ADMIN_SENHA
        )

        db.session.commit()

        print('==========================================')
        print(' ADMINISTRADOR ENCONTRADO')
        print('==========================================')
        print(f' Email: {ADMIN_EMAIL}')
        print(f' Senha: {ADMIN_SENHA}')
        print(' is_admin: True')
        print('==========================================')


# =========================================================
# ROTA PRINCIPAL / LOJA
# =========================================================

@app.route('/')
def index():

    query = request.args.get('q', '').strip()

    if query:

        videos = Video.query.filter(
            Video.titulo.ilike(f'%{query}%')
        ).all()

    else:

        videos = Video.query.all()

    return render_template(
        'index.html',
        videos=videos
    )


# =========================================================
# PROCESSAR PEDIDO
# =========================================================

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

        flash(
            f'Pedido recebido! Entraremos em contato pelo WhatsApp ({whatsapp}).',
            'success'
        )

        return redirect(
            url_for('index')
        )

    except Exception as e:

        db.session.rollback()

        print(
            f'Erro ao cadastrar pedido: {e}'
        )

        flash(
            'Ocorreu um erro ao enviar seu pedido. Tente novamente.',
            'danger'
        )

        return redirect(
            url_for('index')
        )


# =========================================================
# LOGIN - SOMENTE ADMINISTRADOR
# =========================================================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get(
            'email',
            ''
        ).strip().lower()

        senha = request.form.get(
            'senha',
            ''
        )

        print('==========================================')
        print(' TENTATIVA DE LOGIN')
        print('==========================================')
        print(f'Email informado: {email}')
        print('==========================================')

        user = Usuario.query.filter_by(
            email=email
        ).first()

        # -------------------------------------------------
        # Verifica se o usuário existe
        # -------------------------------------------------

        if not user:

            print('LOGIN: usuário não encontrado')

            flash(
                'Acesso negado. Credenciais inválidas.',
                'danger'
            )

            return render_template(
                'login.html'
            )

        # -------------------------------------------------
        # Verifica a senha
        # -------------------------------------------------

        senha_correta = check_password_hash(
            user.senha,
            senha
        )

        # -------------------------------------------------
        # Verifica se é administrador
        # -------------------------------------------------

        if not user.is_admin:

            print('LOGIN: usuário não é administrador')

            flash(
                'Este usuário não possui acesso administrativo.',
                'danger'
            )

            return render_template(
                'login.html'
            )

        # -------------------------------------------------
        # Login autorizado
        # -------------------------------------------------

        if senha_correta:

            print('LOGIN: sucesso')

            session['user_id'] = user.id
            session['user_name'] = user.nome
            session['is_admin'] = True

            return redirect(
                url_for('admin_dashboard')
            )

        # -------------------------------------------------
        # Senha incorreta
        # -------------------------------------------------

        print('LOGIN: senha incorreta')

        flash(
            'Acesso negado. Senha incorreta.',
            'danger'
        )

    return render_template(
        'login.html'
    )


# =========================================================
# PAINEL ADMINISTRATIVO
# =========================================================

@app.route('/admin/dashboard')
def admin_dashboard():

    if not session.get('is_admin'):

        return redirect(
            url_for('login')
        )

    videos = Video.query.all()

    pedidos = Pedido.query.order_by(
        Pedido.id.desc()
    ).all()

    return render_template(
        'admin/dashboard.html',
        videos=videos,
        pedidos=pedidos
    )


# =========================================================
# ADICIONAR VÍDEO
# =========================================================

@app.route('/admin/videos/novo', methods=['POST'])
def adicionar_video():

    if not session.get('is_admin'):

        return redirect(
            url_for('login')
        )

    titulo = request.form.get(
        'titulo',
        ''
    ).strip()

    descricao = request.form.get(
        'descricao',
        ''
    ).strip()

    preco_texto = request.form.get(
        'preco',
        '0'
    )

    file = request.files.get(
        'file'
    )

    # -----------------------------------------------------
    # Converte preço
    # -----------------------------------------------------

    try:

        preco = float(
            preco_texto.replace(',', '.')
        )

    except (ValueError, AttributeError):

        flash(
            'Preço inválido.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )

    # -----------------------------------------------------
    # Verifica arquivo
    # -----------------------------------------------------

    if not file or not file.filename:

        flash(
            'Selecione um arquivo de vídeo.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )

    filename = secure_filename(
        file.filename
    )

    if not filename:

        flash(
            'Nome de arquivo inválido.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )

    # -----------------------------------------------------
    # Salva arquivo
    # -----------------------------------------------------

    caminho_arquivo = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )

    try:

        file.save(
            caminho_arquivo
        )

        # -------------------------------------------------
        # Cria registro no banco
        # -------------------------------------------------

        novo_video = Video(
            titulo=titulo,
            descricao=descricao,
            preco=preco,
            filename=filename
        )

        db.session.add(
            novo_video
        )

        db.session.commit()

        flash(
            'Vídeo cadastrado com sucesso!',
            'success'
        )

    except Exception as e:

        db.session.rollback()

        print(
            f'Erro ao cadastrar vídeo: {e}'
        )

        # Se salvou o arquivo mas o banco falhou,
        # tenta apagar o arquivo
        if os.path.exists(caminho_arquivo):

            try:

                os.remove(
                    caminho_arquivo
                )

            except Exception as erro_arquivo:

                print(
                    f'Erro ao remover arquivo: {erro_arquivo}'
                )

        flash(
            'Erro ao cadastrar vídeo.',
            'danger'
        )

    return redirect(
        url_for('admin_dashboard')
    )


# =========================================================
# EXCLUIR VÍDEO
# =========================================================

@app.route(
    '/excluir_video/<int:id>',
    methods=['POST']
)
def excluir_video(id):

    if not session.get('is_admin'):

        return redirect(
            url_for('login')
        )

    video = Video.query.get_or_404(
        id
    )

    caminho_arquivo = os.path.join(
        app.config['UPLOAD_FOLDER'],
        video.filename
    )

    # -----------------------------------------------------
    # Remove arquivo físico
    # -----------------------------------------------------

    if os.path.exists(caminho_arquivo):

        try:

            os.remove(
                caminho_arquivo
            )

        except Exception as e:

            print(
                f'Erro ao excluir arquivo físico: {e}'
            )

    # -----------------------------------------------------
    # Remove registro do banco
    # -----------------------------------------------------

    try:

        db.session.delete(
            video
        )

        db.session.commit()

        flash(
            'Vídeo excluído com sucesso!',
            'success'
        )

    except Exception as e:

        db.session.rollback()

        print(
            f'Erro ao excluir vídeo do banco: {e}'
        )

        flash(
            'Erro ao excluir do banco de dados.',
            'danger'
        )

    return redirect(
        url_for('admin_dashboard')
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route('/logout')
def logout():

    session.clear()

    return redirect(
        url_for('index')
    )


# =========================================================
# EXECUÇÃO LOCAL
# =========================================================

if __name__ == '__main__':

    app.run(
        debug=True
    )
