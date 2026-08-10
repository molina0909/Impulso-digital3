import os
import uuid

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

app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'sua_chave_secreta_super_segura_aqui'
)


# =========================================================
# DIRETÓRIO BASE
# =========================================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)


# =========================================================
# BANCO SQLITE
# =========================================================

DATABASE_PATH = os.path.join(
    BASE_DIR,
    'plataforma.db'
)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    'sqlite:///' + DATABASE_PATH
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# =========================================================
# CONFIGURAÇÃO DOS UPLOADS
# =========================================================
#
# Para o teste atual:
#
# static/uploads
#
# Quando você colocar em uma hospedagem definitiva,
# poderá definir uma variável de ambiente:
#
# UPLOAD_FOLDER=/caminho/da/pasta/uploads
#
# =========================================================

UPLOAD_FOLDER = os.environ.get(
    'UPLOAD_FOLDER'
)

if not UPLOAD_FOLDER:

    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        'static',
        'uploads'
    )


app.config['UPLOAD_FOLDER'] = os.path.abspath(
    UPLOAD_FOLDER
)


# =========================================================
# LIMITE DE UPLOAD
# =========================================================
#
# 2 GB por requisição.
#
# Isso NÃO significa que o servidor precisa ter 2 GB
# disponíveis na memória.
#
# O Flask/Werkzeug trabalha com o upload como arquivo.
#
# O limite final também pode depender da hospedagem,
# proxy ou servidor web.
#
# =========================================================

app.config['MAX_CONTENT_LENGTH'] = (
    2 * 1024 * 1024 * 1024
)


# =========================================================
# EXTENSÕES PERMITIDAS
# =========================================================

ALLOWED_VIDEO_EXTENSIONS = {
    'mp4'
}


# =========================================================
# CRIA PASTA DE UPLOAD
# =========================================================

try:

    os.makedirs(
        app.config['UPLOAD_FOLDER'],
        exist_ok=True
    )

    print(
        '=========================================='
    )

    print(
        ' PASTA DE UPLOAD'
    )

    print(
        '=========================================='
    )

    print(
        f"Diretório: {app.config['UPLOAD_FOLDER']}"
    )

    print(
        '=========================================='
    )

except Exception as e:

    print(
        'ERRO AO CRIAR PASTA DE UPLOAD:'
    )

    print(e)


# =========================================================
# BANCO
# =========================================================

db.init_app(app)


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def arquivo_permitido(filename):
    """
    Verifica se o arquivo possui uma extensão permitida.
    """

    if not filename:
        return False

    if '.' not in filename:
        return False

    extensao = filename.rsplit(
        '.',
        1
    )[1].lower()

    return extensao in ALLOWED_VIDEO_EXTENSIONS


def gerar_nome_video(filename):
    """
    Gera um nome seguro e único para o vídeo.

    Exemplo:

    video.mp4

    vira:

    video_8f31a4c7d2.mp4
    """

    filename_seguro = secure_filename(
        filename
    )

    if not filename_seguro:
        return None

    nome_original, extensao = os.path.splitext(
        filename_seguro
    )

    identificador = uuid.uuid4().hex

    return (
        f'{nome_original}_{identificador}'
        f'{extensao.lower()}'
    )


def tamanho_arquivo(caminho):
    """
    Retorna o tamanho do arquivo em MB.
    """

    try:

        tamanho_bytes = os.path.getsize(
            caminho
        )

        return tamanho_bytes / (
            1024 * 1024
        )

    except Exception:

        return 0


# =========================================================
# INICIALIZAÇÃO DO BANCO
# =========================================================

with app.app_context():

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

        db.session.add(
            novo_admin
        )

        db.session.commit()

        print(
            '=========================================='
        )

        print(
            ' ADMINISTRADOR CRIADO'
        )

        print(
            '=========================================='
        )

        print(
            f' Email: {ADMIN_EMAIL}'
        )

        print(
            f' Senha: {ADMIN_SENHA}'
        )

        print(
            '=========================================='
        )

    else:

        admin_existente.is_admin = True

        admin_existente.senha = (
            generate_password_hash(
                ADMIN_SENHA
            )
        )

        db.session.commit()

        print(
            '=========================================='
        )

        print(
            ' ADMINISTRADOR ENCONTRADO'
        )

        print(
            '=========================================='
        )

        print(
            f' Email: {ADMIN_EMAIL}'
        )

        print(
            f' Senha: {ADMIN_SENHA}'
        )

        print(
            ' is_admin: True'
        )

        print(
            '=========================================='
        )


# =========================================================
# ROTA PRINCIPAL
# =========================================================

@app.route('/')
def index():

    query = request.args.get(
        'q',
        ''
    ).strip()

    if query:

        videos = Video.query.filter(
            Video.titulo.ilike(
                f'%{query}%'
            )
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

@app.route(
    '/processar_pedido',
    methods=['POST']
)
def processar_pedido():

    pacote = request.form.get(
        'pacote'
    )

    nome = request.form.get(
        'nome'
    )

    email = request.form.get(
        'email'
    )

    whatsapp = request.form.get(
        'whatsapp'
    )

    novo_pedido = Pedido(
        pacote=pacote,
        nome_cliente=nome,
        email_cliente=email,
        whatsapp_cliente=whatsapp,
        status='Aguardando Pagamento'
    )

    try:

        db.session.add(
            novo_pedido
        )

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
            'ERRO AO CADASTRAR PEDIDO:'
        )

        print(e)

        flash(
            'Ocorreu um erro ao enviar seu pedido. Tente novamente.',
            'danger'
        )

        return redirect(
            url_for('index')
        )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    '/login',
    methods=['GET', 'POST']
)
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

        print(
            '=========================================='
        )

        print(
            ' TENTATIVA DE LOGIN'
        )

        print(
            '=========================================='
        )

        print(
            f'Email informado: {email}'
        )

        print(
            '=========================================='
        )

        user = Usuario.query.filter_by(
            email=email
        ).first()

        if not user:

            print(
                'LOGIN: usuário não encontrado'
            )

            flash(
                'Acesso negado. Credenciais inválidas.',
                'danger'
            )

            return render_template(
                'login.html'
            )

        senha_correta = check_password_hash(
            user.senha,
            senha
        )

        if not user.is_admin:

            print(
                'LOGIN: usuário não é administrador'
            )

            flash(
                'Este usuário não possui acesso administrativo.',
                'danger'
            )

            return render_template(
                'login.html'
            )

        if senha_correta:

            print(
                'LOGIN: sucesso'
            )

            session['user_id'] = user.id
            session['user_name'] = user.nome
            session['is_admin'] = True

            return redirect(
                url_for('admin_dashboard')
            )

        print(
            'LOGIN: senha incorreta'
        )

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

@app.route(
    '/admin/videos/novo',
    methods=['POST']
)
def adicionar_video():

    # -----------------------------------------------------
    # VERIFICA ADMIN
    # -----------------------------------------------------

    if not session.get('is_admin'):

        return redirect(
            url_for('login')
        )


    # -----------------------------------------------------
    # DADOS DO FORMULÁRIO
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # VALIDA TÍTULO
    # -----------------------------------------------------

    if not titulo:

        flash(
            'Informe o título do vídeo.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )


    # -----------------------------------------------------
    # CONVERTE PREÇO
    # -----------------------------------------------------

    try:

        preco = float(
            preco_texto.replace(
                ',',
                '.'
            )
        )

    except (
        ValueError,
        AttributeError
    ):

        flash(
            'Preço inválido.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )


    # -----------------------------------------------------
    # PEGA ARQUIVO
    # -----------------------------------------------------

    file = request.files.get(
        'file'
    )


    # -----------------------------------------------------
    # VERIFICA ARQUIVO
    # -----------------------------------------------------

    if not file:

        print(
            'UPLOAD: nenhum arquivo recebido.'
        )

        flash(
            'Nenhum arquivo foi enviado.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )


    if not file.filename:

        print(
            'UPLOAD: arquivo sem nome.'
        )

        flash(
            'Selecione um arquivo de vídeo.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )


    print(
        '=========================================='
    )

    print(
        ' NOVO UPLOAD'
    )

    print(
        '=========================================='
    )

    print(
        f'Arquivo original: {file.filename}'
    )


    # -----------------------------------------------------
    # VERIFICA EXTENSÃO
    # -----------------------------------------------------

    if not arquivo_permitido(
        file.filename
    ):

        print(
            'UPLOAD: extensão não permitida.'
        )

        flash(
            'Formato inválido. Envie somente arquivos MP4.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )


    # -----------------------------------------------------
    # GERA NOME ÚNICO
    # -----------------------------------------------------

    filename = gerar_nome_video(
        file.filename
    )

    if not filename:

        print(
            'UPLOAD: não foi possível gerar nome seguro.'
        )

        flash(
            'Nome de arquivo inválido.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )


    # -----------------------------------------------------
    # CAMINHO FINAL
    # -----------------------------------------------------

    caminho_arquivo = os.path.join(
        app.config['UPLOAD_FOLDER'],
        filename
    )


    print(
        f'Nome salvo: {filename}'
    )

    print(
        f'Caminho: {caminho_arquivo}'
    )


    # -----------------------------------------------------
    # GARANTE QUE A PASTA EXISTE
    # -----------------------------------------------------

    try:

        os.makedirs(
            app.config['UPLOAD_FOLDER'],
            exist_ok=True
        )

    except Exception as e:

        print(
            'ERRO AO CRIAR PASTA:'
        )

        print(e)

        flash(
            'Não foi possível criar a pasta de uploads.',
            'danger'
        )

        return redirect(
            url_for('admin_dashboard')
        )


    # -----------------------------------------------------
    # SALVA O ARQUIVO
    # -----------------------------------------------------

    arquivo_salvo = False

    try:

        file.save(
            caminho_arquivo
        )

        # -----------------------------------------------
        # CONFIRMA QUE O ARQUIVO EXISTE
        # -----------------------------------------------

        if not os.path.exists(
            caminho_arquivo
        ):

            raise Exception(
                'O arquivo não existe após o upload.'
            )


        # -----------------------------------------------
        # CONFIRMA QUE NÃO ESTÁ VAZIO
        # -----------------------------------------------

        tamanho = os.path.getsize(
            caminho_arquivo
        )

        if tamanho <= 0:

            raise Exception(
                'O arquivo foi criado, mas possui 0 bytes.'
            )


        arquivo_salvo = True


        tamanho_mb = tamanho_arquivo(
            caminho_arquivo
        )


        print(
            'UPLOAD: arquivo salvo com sucesso.'
        )

        print(
            f'Tamanho: {tamanho_mb:.2f} MB'
        )


        # ------------------------------------------------
        # CRIA REGISTRO NO BANCO
        # ------------------------------------------------

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


        print(
            'UPLOAD: registro salvo no banco.'
        )

        print(
            '=========================================='
        )


        flash(
            f'Vídeo cadastrado com sucesso! '
            f'Arquivo salvo ({tamanho_mb:.1f} MB).',
            'success'
        )


    except Exception as e:

        print(
            '=========================================='
        )

        print(
            ' ERRO NO UPLOAD'
        )

        print(
            '=========================================='
        )

        print(
            repr(e)
        )

        print(
            '=========================================='
        )


        # -----------------------------------------------
        # DESFAZ BANCO
        # -----------------------------------------------

        db.session.rollback()


        # -----------------------------------------------
        # REMOVE ARQUIVO SE O BANCO FALHOU
        # -----------------------------------------------

        if arquivo_salvo and os.path.exists(
            caminho_arquivo
        ):

            try:

                os.remove(
                    caminho_arquivo
                )

                print(
                    'Arquivo removido após erro.'
                )

            except Exception as erro_arquivo:

                print(
                    'Erro ao remover arquivo:'
                )

                print(
                    repr(erro_arquivo)
                )


        flash(
            f'Erro ao cadastrar vídeo: {str(e)}',
            'danger'
        )


    return redirect(
        url_for('admin_dashboard')
    )


# =========================================================
# ERRO DE ARQUIVO GRANDE
# =========================================================

@app.errorhandler(413)
def arquivo_muito_grande(error):

    print(
        'UPLOAD: arquivo excedeu o limite de 2 GB.'
    )

    flash(
        'O vídeo é muito grande. O limite configurado é de 2 GB.',
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
    # REMOVE ARQUIVO FÍSICO
    # -----------------------------------------------------

    if os.path.exists(
        caminho_arquivo
    ):

        try:

            os.remove(
                caminho_arquivo
            )

            print(
                f'Arquivo removido: {caminho_arquivo}'
            )

        except Exception as e:

            print(
                'Erro ao excluir arquivo físico:'
            )

            print(
                repr(e)
            )


    # -----------------------------------------------------
    # REMOVE BANCO
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
            'Erro ao excluir vídeo do banco:'
        )

        print(
            repr(e)
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
        host='0.0.0.0',
        port=int(
            os.environ.get(
                'PORT',
                5000
            )
        ),
        debug=True
    )
