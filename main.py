from flask import Flask, render_template
from databaser import criar_tabelas
from routes.user import user_bp

criar_tabelas()

main = Flask(__name__)
main.secret_key = 'minha_chave_super_secreta_123'

@main.route('/')
def telaInicial():
    return render_template('telainicial.html')

main.register_blueprint(user_bp, url_prefix='/user')

if __name__ == '__main__':
    main.run(debug=True)
