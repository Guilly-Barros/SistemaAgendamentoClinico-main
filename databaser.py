import sqlite3
from werkzeug.security import generate_password_hash

def conectar():
    return sqlite3.connect('databaser.db')

def conectar():
    conn = sqlite3.connect('databaser.db')
    conn.row_factory = sqlite3.Row  # <- faz retornar dicionários
    return conn

def criar_tabelas():
    conn = sqlite3.connect('databaser.db')
    cursor = conn.cursor()

    # Cria a tabela usuários do zero
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        tipo_usuario TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS procedimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT
    )
    ''')
    # Salas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS salas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        capacidade INTEGER
    )
    ''')
    # Agendamentos
    cursor.execute('''
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

 # Verifica se já existe um recepcionista master
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", ("recepcionistamaster@gmail.com",))
    master = cursor.fetchone()

    if not master:
        cursor.execute('''
            INSERT INTO usuarios (nome, email, senha, tipo_usuario)
            VALUES (?, ?, ?, ?)
        ''', ("Recepcionista Master", "recepcionistamaster@gmail.com", "12345", "recepcionista"))
        print(" Usuário recepcionista master criado com sucesso!")
    else:
        print("ℹ Usuário recepcionista master já existe no banco.")

    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    criar_tabelas()
    print("Tabelas criadas com sucesso!")