from flask import Blueprint, Flask, render_template, session    
from routes.user import user_bp
from databaser import criar_tabelas

criar_tabelas()
main = Flask(__name__) 
main.secret_key = 'minha_chave_super_secreta_123'  # qualquer texto único


@main.route("/")
def telaInicial():
    return render_template("telainicial.html")

main.register_blueprint(user_bp, url_prefix='/user') 


if __name__ == "__main__":
    main.run(debug=True)