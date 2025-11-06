from dbm import sqlite3
from flask import Blueprint, redirect, render_template, request, session, url_for, flash
from databaser import conectar
from functools import wraps
user_bp = Blueprint('user', __name__, template_folder='templates') 

# Função auxiliar para proteger rotas
def login_required(role=None):
    def wrapper(fn):
        def decorated_view(*args, **kwargs):
            if 'usuario_id' not in session:
                return redirect(url_for('user.user'))  # redireciona pro login se não tiver logado

            if role and session.get('usuario_tipo') != role:
                return redirect(url_for('user.user'))  # impede acesso de outro tipo de usuário

            return fn(*args, **kwargs)
        decorated_view.__name__ = fn.__name__
        return decorated_view
    return wrapper

@user_bp.route("/", methods=["GET", "POST"])
def user():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        conn = conectar()
        cursor = conn.cursor()

        # busca o usuário com base no email e senha
        cursor.execute("SELECT id, nome, tipo_usuario FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
        usuario = cursor.fetchone()

        if usuario:
            # salva dados na sessão
            session["usuario_id"] = usuario[0]
            session["usuario_nome"] = usuario[1]
            session["usuario_tipo"] = usuario[2].lower()

            # redireciona conforme o tipo
            if usuario[2].lower() == "medico":
                return redirect(url_for("user.visao_medico"))
            elif usuario[2].lower() == "paciente":
                return redirect(url_for("user.visao_paciente"))
            elif usuario[2].lower() in ["recepcionista", "recepcionista master"]:
                return redirect(url_for("user.visao_recepcionista"))
            else:
                flash("Tipo de usuário desconhecido!", "danger")
        else:
            flash("E-mail ou senha incorretos!", "danger")

        conn.close()

    return render_template("login.html")

@user_bp.route("/agendar_consulta", methods=["GET", "POST"])
def agendar_consulta():
    conn = conectar()
    cur = conn.cursor()

    # Carregar os dados das tabelas relacionadas
    cur.execute("SELECT id, nome FROM usuarios WHERE tipo_usuario = 'paciente'")
    pacientes = cur.fetchall()

    cur.execute("SELECT id, nome FROM usuarios WHERE tipo_usuario = 'medico'")
    medicos = cur.fetchall()

    cur.execute("SELECT id, nome FROM procedimentos")
    procedimentos = cur.fetchall()

    cur.execute("SELECT id, nome FROM salas")
    salas = cur.fetchall()

    if request.method == "POST":
        paciente_id = request.form["paciente_id"]
        medico_id = request.form["medico_id"]
        procedimento_id = request.form["procedimento_id"]
        sala_id = request.form["sala_id"]
        data = request.form["data"]
        hora = request.form["hora"]

        # Verificar se já existe agendamento no mesmo horário e sala
        cur.execute("""
            SELECT * FROM agendamentos 
            WHERE data = ? AND hora = ? AND sala_id = ?
        """, (data, hora, sala_id))
        conflito = cur.fetchone()

        if conflito:
            flash("Já existe uma consulta marcada para essa sala nesse horário!", "danger")
        else:
            cur.execute("""
                INSERT INTO agendamentos (paciente_id, medico_id, procedimento_id, sala_id, data, hora)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (paciente_id, medico_id, procedimento_id, sala_id, data, hora))
            conn.commit()
            flash("Consulta agendada com sucesso!", "success")

        conn.close()
        return redirect(url_for("user.agendar_consulta"))

    conn.close()
    return render_template(
        "agendamentoConsulta.html",
        pacientes=pacientes,
        medicos=medicos,
        procedimentos=procedimentos,
        salas=salas
    )
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
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]
        tipo_usuario = "paciente"  # fixo por enquanto

        conn = conectar()
        cursor = conn.cursor()

        # Salva no banco de dados
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo_usuario) VALUES (?, ?, ?, ?)",
            (nome, email, senha, tipo_usuario)
        )
        conn.commit()
        conn.close()

        print(f"Novo paciente cadastrado: {nome} - {email}")
        
        # Depois do cadastro, redireciona para a tela de login
        return redirect(url_for("user.user"))

    # Se for GET, mostra o formulário de cadastro
    return render_template("register.html")


# CADASTRO DE USUÁRIOS (painel da recepcionista)
@user_bp.route("/cadastrar_usuarios", methods=["GET", "POST"])
def cadastrar_usuarios():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]
        tipo_usuario = request.form["tipo_usuario"]

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo_usuario) VALUES (?, ?, ?, ?)",
            (nome, email, senha, tipo_usuario)
        )
        conn.commit()
        conn.close()

        print(f"Usuário cadastrado: {nome} ({tipo_usuario})")
        return redirect(url_for("user.visao_recepcionista"))

    return render_template("cadastrarUsuarios.html")