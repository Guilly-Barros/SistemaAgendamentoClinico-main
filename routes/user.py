from flask import Blueprint, redirect, render_template, request, session, url_for, flash
from databaser import conectar, criar_tabelas
from functools import wraps
from werkzeug.security import check_password_hash

user_bp = Blueprint('user', __name__, template_folder='templates')

def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('user.user'))
            if role:
                tipo = (session.get('usuario_tipo') or '').lower()
                if role == 'recepcionista':
                    if tipo not in ('recepcionista', 'recepcionista master'):
                        return redirect(url_for('user.user'))
                else:
                    if tipo != role:
                        return redirect(url_for('user.user'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

@user_bp.route("/", methods=["GET", "POST"])
def user():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, tipo_usuario, senha FROM usuarios WHERE email = ?", (email,))
        usuario = cursor.fetchone()

        if usuario:
            senha_db = usuario["senha"]
            ok = False
            try:
                ok = check_password_hash(senha_db, senha)
            except Exception:
                ok = False
            if not ok:
                ok = (senha_db == senha)  # compatibilidade com senhas antigas sem hash

            if ok:
                session["usuario_id"] = usuario["id"]
                session["usuario_nome"] = usuario["nome"]
                session["usuario_tipo"] = (usuario["tipo_usuario"] or "").lower()

                tipo = session["usuario_tipo"]
                if tipo == "medico":
                    return redirect(url_for("user.visao_medico"))
                elif tipo == "paciente":
                    return redirect(url_for("user.visao_paciente"))
                elif tipo in ("recepcionista", "recepcionista master"):
                    return redirect(url_for("user.visao_recepcionista"))
                else:
                    flash("Tipo de usuário desconhecido!", "danger")
            else:
                flash("E-mail ou senha incorretos!", "danger")
        else:
            flash("E-mail ou senha incorretos!", "danger")
        conn.close()
    return render_template("login.html")

@user_bp.route("/agendar_consulta", methods=["GET", "POST"])
@login_required(role='recepcionista')
def agendar_consulta():
    # Garante estrutura/seed a cada acesso (idempotente)
    criar_tabelas()

    conn = conectar()
    cur = conn.cursor()

    cur.execute("SELECT id, nome FROM usuarios WHERE tipo_usuario = 'paciente'")
    pacientes = cur.fetchall()

    cur.execute("SELECT id, nome FROM usuarios WHERE tipo_usuario IN ('medico','médico')")
    medicos = cur.fetchall()

    cur.execute("SELECT id, nome FROM procedimentos")
    procedimentos = cur.fetchall()

    cur.execute("SELECT id, nome FROM salas")
    salas = cur.fetchall()

    if request.method == "POST":
        paciente_id = request.form.get("paciente_id")
        medico_id = request.form.get("medico_id")
        procedimento_id = request.form.get("procedimento_id")
        sala_id = request.form.get("sala_id")
        data = request.form.get("data")
        hora = request.form.get("hora")

        # Campos extras do front (conforme escolha)
        convenio_subtipo = request.form.get("convenio_subtipo")
        medico_receita_id = request.form.get("medico_receita_id")
        valor_particular = request.form.get("valor_particular")

        # Se veio um fallback textual (__particular__/__convenio__/__receita__), converte para ID real
        if not (procedimento_id or "").isdigit():
            nome_map = {
                "__particular__": "Consulta Particular",
                "__convenio__":  "Consulta Convênio",
                "__receita__":   "Solicitação de Receita",
            }
            nome = nome_map.get(procedimento_id, procedimento_id)
            cur.execute("SELECT id FROM procedimentos WHERE nome = ?", (nome,))
            row = cur.fetchone()
            if row:
                procedimento_id = str(row["id"])
            else:
                cur.execute("INSERT INTO procedimentos (nome, descricao) VALUES (?, ?)", (nome, ""))
                conn.commit()
                procedimento_id = str(cur.lastrowid)

        # Conflito de sala/data/hora
        cur.execute("SELECT 1 FROM agendamentos WHERE data = ? AND hora = ? AND sala_id = ?", (data, hora, sala_id))
        conflito = cur.fetchone()

        if conflito:
            flash("Já existe uma consulta marcada para essa sala nesse horário!", "danger")
        else:
            cur.execute(
                "INSERT INTO agendamentos (paciente_id, medico_id, procedimento_id, sala_id, data, hora) VALUES (?, ?, ?, ?, ?, ?)",
                (paciente_id, medico_id, procedimento_id, sala_id, data, hora)
            )
            conn.commit()
            flash("Consulta agendada com sucesso!", "success")

        conn.close()
        return redirect(url_for("user.agendar_consulta"))

    conn.close()
    return render_template("agendamentoConsulta.html", pacientes=pacientes, medicos=medicos, procedimentos=procedimentos, salas=salas)

@user_bp.route("/recepcionista")
@login_required(role='recepcionista')
def visao_recepcionista():
    return render_template("recepcionista.html")

@user_bp.route("/medico")
@login_required(role='medico')
def visao_medico():
    return render_template("medico.html")

@user_bp.route("/paciente")
@login_required(role='paciente')
def visao_paciente():
    return render_template("paciente.html")

@user_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        from werkzeug.security import generate_password_hash
        senha_hash = generate_password_hash(senha)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo_usuario) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, "paciente")
        )
        conn.commit()
        conn.close()

        flash("Cadastro realizado! Faça login para continuar.", "success")
        return redirect(url_for("user.user"))

    return render_template("register.html")

@user_bp.route("/cadastrar_usuarios", methods=["GET", "POST"])
@login_required(role='recepcionista')
def cadastrar_usuarios():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        tipo_usuario = request.form.get("tipo_usuario", "").lower()

        from werkzeug.security import generate_password_hash
        senha_hash = generate_password_hash(senha)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo_usuario) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo_usuario)
        )
        conn.commit()
        conn.close()

        flash(f"Usuário cadastrado: {nome} ({tipo_usuario})", "success")
        return redirect(url_for("user.visao_recepcionista"))

    return render_template("cadastrarUsuarios.html")
