import os
import uuid
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   flash, session, send_from_directory, abort)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ─────────────────────────────────────────────
# Configuração da aplicação
# ─────────────────────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'jccolchao-secret-2024-change-in-prod')

# ── Banco de dados ───────────────────────────────────────────────────────────
# Em produção (Railway) usa DATABASE_URL; localmente usa SQLite
DATABASE_URL = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'jccolchao.db')}")
# Railway retorna "postgres://" que precisa ser "postgresql://"
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ── Upload de arquivos ───────────────────────────────────────────────────────
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'xml'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

db = SQLAlchemy(app)

# ─────────────────────────────────────────────
# Modelos
# ─────────────────────────────────────────────

class Fornecedor(db.Model):
    """Usuário / Fornecedor do portal."""
    __tablename__ = 'fornecedores'

    id            = db.Column(db.Integer, primary_key=True)
    razao_social  = db.Column(db.String(200), nullable=False)
    cnpj          = db.Column(db.String(20), unique=True, nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    telefone      = db.Column(db.String(20))
    contato       = db.Column(db.String(100))          # nome do responsável
    senha_hash    = db.Column(db.String(256), nullable=False)
    ativo         = db.Column(db.Boolean, default=True)
    criado_em     = db.Column(db.DateTime, default=datetime.utcnow)
    agendamentos  = db.relationship('Agendamento', backref='fornecedor', lazy=True)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


class Agendamento(db.Model):
    """Agendamento de entrega feito pelo fornecedor."""
    __tablename__ = 'agendamentos'

    id                  = db.Column(db.Integer, primary_key=True)
    codigo              = db.Column(db.String(20), unique=True, nullable=False)
    fornecedor_id       = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=False)

    # Dados da entrega
    data_entrega        = db.Column(db.Date, nullable=False)
    hora_entrega        = db.Column(db.String(10), nullable=False)
    num_nota_fiscal     = db.Column(db.String(50), nullable=False)
    valor_nota          = db.Column(db.Float, nullable=False)
    qtd_volumes         = db.Column(db.Integer, nullable=False)
    peso_total_kg       = db.Column(db.Float)
    tipo_mercadoria     = db.Column(db.String(200))
    observacoes         = db.Column(db.Text)

    # Dados do veículo / transportadora
    transportadora      = db.Column(db.String(150))
    placa_veiculo       = db.Column(db.String(15))
    nome_motorista      = db.Column(db.String(100))
    cpf_motorista       = db.Column(db.String(15))

    # Arquivo da nota fiscal
    arquivo_nf          = db.Column(db.String(300))    # nome do arquivo salvo
    arquivo_nf_original = db.Column(db.String(300))    # nome original

    # Status
    status              = db.Column(db.String(30), default='Aguardando Aprovação')
    # Aguardando Aprovação | Aprovado | Reprovado | Cancelado | Entregue

    criado_em           = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Motivo de reprovação / observação do admin
    obs_admin           = db.Column(db.Text)


class Admin(db.Model):
    """Usuário administrador do portal (equipe JC Colchão)."""
    __tablename__ = 'admins'

    id         = db.Column(db.Integer, primary_key=True)
    nome       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    criado_em  = db.Column(db.DateTime, default=datetime.utcnow)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def arquivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def gerar_codigo():
    """Gera um código único de agendamento ex: AGD-20240901-A3F2."""
    hoje = datetime.now().strftime('%Y%m%d')
    sufixo = uuid.uuid4().hex[:4].upper()
    return f"AGD-{hoje}-{sufixo}"


# ─────────────────────────────────────────────
# Decoradores de autenticação
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'fornecedor_id' not in session:
            flash('Faça login para continuar.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Acesso restrito. Faça login como administrador.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


def fornecedor_atual():
    if 'fornecedor_id' in session:
        return Fornecedor.query.get(session['fornecedor_id'])
    return None


def admin_atual():
    if 'admin_id' in session:
        return Admin.query.get(session['admin_id'])
    return None


# ─────────────────────────────────────────────
# Contexto global de templates
# ─────────────────────────────────────────────

@app.context_processor
def inject_globals():
    return dict(
        fornecedor_atual=fornecedor_atual(),
        admin_atual=admin_atual(),
        ano_atual=datetime.now().year
    )


# ─────────────────────────────────────────────
# Rotas Públicas
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ── Login de Fornecedor ──────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'fornecedor_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')

        fornecedor = Fornecedor.query.filter_by(email=email).first()
        if fornecedor and fornecedor.verificar_senha(senha):
            if not fornecedor.ativo:
                flash('Sua conta está inativa. Entre em contato com a JC Colchão.', 'danger')
                return redirect(url_for('login'))
            session['fornecedor_id'] = fornecedor.id
            flash(f'Bem-vindo(a), {fornecedor.razao_social}!', 'success')
            return redirect(url_for('dashboard'))
        flash('E-mail ou senha inválidos.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('fornecedor_id', None)
    flash('Você saiu do portal.', 'info')
    return redirect(url_for('login'))


# ── Cadastro de Fornecedor ──────────────────

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'fornecedor_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        razao   = request.form.get('razao_social', '').strip()
        cnpj    = request.form.get('cnpj', '').strip()
        email   = request.form.get('email', '').strip().lower()
        tel     = request.form.get('telefone', '').strip()
        contato = request.form.get('contato', '').strip()
        senha   = request.form.get('senha', '')
        conf    = request.form.get('confirmar_senha', '')

        erros = []
        if not razao:   erros.append('Razão social obrigatória.')
        if not cnpj:    erros.append('CNPJ obrigatório.')
        if not email:   erros.append('E-mail obrigatório.')
        if len(senha) < 6: erros.append('Senha deve ter ao menos 6 caracteres.')
        if senha != conf:   erros.append('As senhas não coincidem.')
        if Fornecedor.query.filter_by(cnpj=cnpj).first():
            erros.append('CNPJ já cadastrado.')
        if Fornecedor.query.filter_by(email=email).first():
            erros.append('E-mail já cadastrado.')

        if erros:
            for e in erros:
                flash(e, 'danger')
            return render_template('cadastro.html', form=request.form)

        novo = Fornecedor(
            razao_social=razao,
            cnpj=cnpj,
            email=email,
            telefone=tel,
            contato=contato
        )
        novo.set_senha(senha)
        db.session.add(novo)
        db.session.commit()

        flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro.html', form={})


# ─────────────────────────────────────────────
# Rotas de Fornecedor (área logada)
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    f = fornecedor_atual()
    agendamentos = (Agendamento.query
                    .filter_by(fornecedor_id=f.id)
                    .order_by(Agendamento.criado_em.desc())
                    .limit(10).all())

    stats = {
        'total':     Agendamento.query.filter_by(fornecedor_id=f.id).count(),
        'aguardando': Agendamento.query.filter_by(fornecedor_id=f.id, status='Aguardando Aprovação').count(),
        'aprovados': Agendamento.query.filter_by(fornecedor_id=f.id, status='Aprovado').count(),
        'entregues': Agendamento.query.filter_by(fornecedor_id=f.id, status='Entregue').count(),
    }
    return render_template('dashboard.html', agendamentos=agendamentos, stats=stats)


@app.route('/novo-agendamento', methods=['GET', 'POST'])
@login_required
def novo_agendamento():
    f = fornecedor_atual()

    if request.method == 'POST':
        # Validações básicas
        data_str   = request.form.get('data_entrega', '')
        hora       = request.form.get('hora_entrega', '')
        num_nf     = request.form.get('num_nota_fiscal', '').strip()
        valor      = request.form.get('valor_nota', '0').replace(',', '.')
        volumes    = request.form.get('qtd_volumes', '0')
        peso       = request.form.get('peso_total_kg', '0').replace(',', '.')
        tipo       = request.form.get('tipo_mercadoria', '').strip()
        obs        = request.form.get('observacoes', '').strip()
        transp     = request.form.get('transportadora', '').strip()
        placa      = request.form.get('placa_veiculo', '').strip()
        motorista  = request.form.get('nome_motorista', '').strip()
        cpf_mot    = request.form.get('cpf_motorista', '').strip()

        erros = []
        if not data_str: erros.append('Data de entrega obrigatória.')
        if not hora:     erros.append('Horário de entrega obrigatório.')
        if not num_nf:   erros.append('Número da nota fiscal obrigatório.')

        # Arquivo NF
        arquivo_nf = request.files.get('arquivo_nf')
        if not arquivo_nf or arquivo_nf.filename == '':
            erros.append('Anexo da nota fiscal é obrigatório.')
        elif not arquivo_permitido(arquivo_nf.filename):
            erros.append('Formato do arquivo inválido. Use PDF, PNG, JPG, JPEG ou XML.')

        if erros:
            for e in erros:
                flash(e, 'danger')
            return render_template('novo_agendamento.html', form=request.form)

        # Salva o arquivo
        nome_original = secure_filename(arquivo_nf.filename)
        ext = nome_original.rsplit('.', 1)[1].lower()
        nome_salvo = f"{uuid.uuid4().hex}.{ext}"
        arquivo_nf.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_salvo))

        try:
            data_entrega = datetime.strptime(data_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Data inválida.', 'danger')
            return render_template('novo_agendamento.html', form=request.form)

        # Validação: Limite de 1 agendamento por horário
        agendamentos_existentes = Agendamento.query.filter(
            Agendamento.data_entrega == data_entrega,
            Agendamento.hora_entrega == hora,
            Agendamento.status.notin_(['Cancelado', 'Reprovado'])
        ).count()

        if agendamentos_existentes >= 1:
            flash('Este horário já não está mais disponível. Por favor, selecione outro.', 'danger')
            return render_template('novo_agendamento.html', form=request.form)

        ag = Agendamento(
            codigo=gerar_codigo(),
            fornecedor_id=f.id,
            data_entrega=data_entrega,
            hora_entrega=hora,
            num_nota_fiscal=num_nf,
            valor_nota=float(valor or 0),
            qtd_volumes=int(volumes or 0),
            peso_total_kg=float(peso or 0),
            tipo_mercadoria=tipo,
            observacoes=obs,
            transportadora=transp,
            placa_veiculo=placa,
            nome_motorista=motorista,
            cpf_motorista=cpf_mot,
            arquivo_nf=nome_salvo,
            arquivo_nf_original=nome_original,
        )
        db.session.add(ag)
        db.session.commit()

        flash(f'Agendamento {ag.codigo} criado com sucesso!', 'success')
        return redirect(url_for('meus_agendamentos'))

    # Datas mínima/máxima para o datepicker
    hoje = datetime.now().date()
    min_data = (hoje + timedelta(days=1)).strftime('%Y-%m-%d')
    max_data = (hoje + timedelta(days=60)).strftime('%Y-%m-%d')

    return render_template('novo_agendamento.html', form={},
                           min_data=min_data, max_data=max_data)


@app.route('/meus-agendamentos')
@login_required
def meus_agendamentos():
    f = fornecedor_atual()
    status_filtro = request.args.get('status', '')
    query = Agendamento.query.filter_by(fornecedor_id=f.id)
    if status_filtro:
        query = query.filter_by(status=status_filtro)
    agendamentos = query.order_by(Agendamento.criado_em.desc()).all()
    return render_template('meus_agendamentos.html', agendamentos=agendamentos,
                           status_filtro=status_filtro)


@app.route('/agendamento/<int:ag_id>')
@login_required
def detalhe_agendamento(ag_id):
    f = fornecedor_atual()
    ag = Agendamento.query.filter_by(id=ag_id, fornecedor_id=f.id).first_or_404()
    return render_template('detalhe_agendamento.html', ag=ag)


@app.route('/agendamento/<int:ag_id>/cancelar', methods=['POST'])
@login_required
def cancelar_agendamento(ag_id):
    f = fornecedor_atual()
    ag = Agendamento.query.filter_by(id=ag_id, fornecedor_id=f.id).first_or_404()
    if ag.status in ('Aguardando Aprovação', 'Aprovado'):
        ag.status = 'Cancelado'
        ag.atualizado_em = datetime.utcnow()
        db.session.commit()
        flash(f'Agendamento {ag.codigo} cancelado.', 'info')
    else:
        flash('Este agendamento não pode ser cancelado.', 'warning')
    return redirect(url_for('meus_agendamentos'))


@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    f = fornecedor_atual()
    if request.method == 'POST':
        f.razao_social = request.form.get('razao_social', f.razao_social).strip()
        f.telefone     = request.form.get('telefone', f.telefone).strip()
        f.contato      = request.form.get('contato', f.contato).strip()

        nova_senha = request.form.get('nova_senha', '')
        conf_senha = request.form.get('confirmar_senha', '')
        if nova_senha:
            if len(nova_senha) < 6:
                flash('Nova senha deve ter ao menos 6 caracteres.', 'danger')
                return render_template('perfil.html')
            if nova_senha != conf_senha:
                flash('As senhas não coincidem.', 'danger')
                return render_template('perfil.html')
            f.set_senha(nova_senha)

        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('perfil'))

    return render_template('perfil.html')


# Download seguro do arquivo NF (somente dono ou admin)
@app.route('/uploads/<filename>')
def download_arquivo(filename):
    # Permite acesso se logado como fornecedor dono ou admin
    ag = Agendamento.query.filter_by(arquivo_nf=filename).first()
    if ag is None:
        abort(404)
    if 'admin_id' not in session:
        if 'fornecedor_id' not in session or ag.fornecedor_id != session['fornecedor_id']:
            abort(403)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename,
                               download_name=ag.arquivo_nf_original)


# ─────────────────────────────────────────────
# Rotas Administrativas
# ─────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_id' in session:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.verificar_senha(senha):
            session['admin_id'] = admin.id
            flash(f'Bem-vindo(a), {admin.nome}!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Credenciais inválidas.', 'danger')

    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect(url_for('admin_login'))


@app.route('/admin')
@admin_required
def admin_dashboard():
    total     = Agendamento.query.count()
    aguardando = Agendamento.query.filter_by(status='Aguardando Aprovação').count()
    aprovados = Agendamento.query.filter_by(status='Aprovado').count()
    entregues = Agendamento.query.filter_by(status='Entregue').count()
    reprovados = Agendamento.query.filter_by(status='Reprovado').count()

    recentes = (Agendamento.query
                .order_by(Agendamento.criado_em.desc())
                .limit(15).all())

    stats = dict(total=total, aguardando=aguardando,
                 aprovados=aprovados, entregues=entregues, reprovados=reprovados)
    return render_template('admin/dashboard.html', stats=stats, recentes=recentes)


@app.route('/admin/agendamentos')
@admin_required
def admin_agendamentos():
    status_filtro = request.args.get('status', '')
    query = Agendamento.query
    if status_filtro:
        query = query.filter_by(status=status_filtro)
    agendamentos = query.order_by(Agendamento.criado_em.desc()).all()
    return render_template('admin/agendamentos.html',
                           agendamentos=agendamentos, status_filtro=status_filtro)


@app.route('/admin/agendamento/<int:ag_id>')
@admin_required
def admin_detalhe(ag_id):
    ag = Agendamento.query.get_or_404(ag_id)
    return render_template('admin/detalhe.html', ag=ag)


@app.route('/admin/agendamento/<int:ag_id>/status', methods=['POST'])
@admin_required
def admin_mudar_status(ag_id):
    ag = Agendamento.query.get_or_404(ag_id)
    novo_status = request.form.get('status', '')
    obs_admin   = request.form.get('obs_admin', '').strip()
    status_validos = ('Aguardando Aprovação', 'Aprovado', 'Reprovado', 'Entregue', 'Cancelado')
    if novo_status in status_validos:
        ag.status = novo_status
        ag.obs_admin = obs_admin
        ag.atualizado_em = datetime.utcnow()
        db.session.commit()
        flash(f'Status atualizado para "{novo_status}".', 'success')
    else:
        flash('Status inválido.', 'danger')
    return redirect(url_for('admin_detalhe', ag_id=ag_id))


@app.route('/admin/fornecedores')
@admin_required
def admin_fornecedores():
    fornecedores = Fornecedor.query.order_by(Fornecedor.razao_social).all()
    return render_template('admin/fornecedores.html', fornecedores=fornecedores)


@app.route('/admin/fornecedor/<int:forn_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_fornecedor(forn_id):
    f = Fornecedor.query.get_or_404(forn_id)
    f.ativo = not f.ativo
    db.session.commit()
    estado = 'ativado' if f.ativo else 'desativado'
    flash(f'Fornecedor {f.razao_social} {estado}.', 'info')
    return redirect(url_for('admin_fornecedores'))


# ─────────────────────────────────────────────
# Inicialização
# ─────────────────────────────────────────────

def criar_admin_padrao():
    """Cria o admin padrão se não existir nenhum."""
    if Admin.query.count() == 0:
        admin = Admin(nome='Administrador JC Colchão', email='admin@jccolchao.com.br')
        admin.set_senha('admin@123')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin padrão criado: admin@jccolchao.com.br / admin@123")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        criar_admin_padrao()
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('FLASK_ENV', 'production') == 'development'
    print(f"[OK] Portal JC Colchao iniciado na porta {PORT}")
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)
