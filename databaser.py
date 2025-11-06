import sqlite3, os
from werkzeug.security import generate_password_hash

# Caminho ABSOLUTO garante que app e seed usem o mesmo arquivo .db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'databaser.db')

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # --- Tabelas ---
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            tipo_usuario TEXT NOT NULL
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS procedimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS salas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            capacidade INTEGER
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            medico_id INTEGER NOT NULL,
            procedimento_id INTEGER NOT NULL,
            sala_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            FOREIGN KEY (paciente_id) REFERENCES usuarios (id),
            FOREIGN KEY (medico_id) REFERENCES usuarios (id),
            FOREIGN KEY (procedimento_id) REFERENCES procedimentos (id),
            FOREIGN KEY (sala_id) REFERENCES salas (id)
        )
    ''')

    # --- Deduplicação preventiva (remove linhas repetidas preservando a 1ª) ---
    cur.execute("""DELETE FROM procedimentos
                   WHERE rowid NOT IN (
                     SELECT MIN(rowid) FROM procedimentos GROUP BY nome
                   )""")
    cur.execute("""DELETE FROM salas
                   WHERE rowid NOT IN (
                     SELECT MIN(rowid) FROM salas GROUP BY nome
                   )""")

    # --- Índices UNIQUE (garantem que não duplique mais no futuro) ---
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_procedimentos_nome ON procedimentos(nome)")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_salas_nome ON salas(nome)")

    # --- Seeds idempotentes ---
    for nome, desc in [
        ("Consulta Particular", "Atendimento particular"),
        ("Consulta Convênio", "Atendimento via convênios cadastrados"),
        ("Solicitação de Receita", "Solicitação/renovação de receita"),
    ]:
        cur.execute("INSERT OR IGNORE INTO procedimentos (nome, descricao) VALUES (?, ?)", (nome, desc))

    for nome, cap in [("Sala 1", 1), ("Sala 2", 1), ("Sala 3", 1)]:
        cur.execute("INSERT OR IGNORE INTO salas (nome, capacidade) VALUES (?, ?)", (nome, cap))

    # Usuário padrão: Recepcionista Master (senha 12345)
    cur.execute("SELECT 1 FROM usuarios WHERE email = ?", ("recepcionistamaster@gmail.com",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo_usuario) VALUES (?, ?, ?, ?)",
            ("Recepcionista Master", "recepcionistamaster@gmail.com", generate_password_hash("12345"), "recepcionista master")
        )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    criar_tabelas()
    print("Banco pronto em", DB_PATH)
