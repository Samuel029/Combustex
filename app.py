from flask import Flask, render_template, request, redirect, url_for, session
from combustiveis.gasolina_adtivada import GasolinaAditivada
import pyqrcode
import pickle
import os

app = Flask(__name__)
app.secret_key = 'Combustex_posto'

USUARIOS_FILE = 'usuarios.pkl'

def load_usuarios():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, 'rb') as file:
            return pickle.load(file)
    return {}

def save_usuarios(usuarios):
    with open(USUARIOS_FILE, 'wb') as file:
        pickle.dump(usuarios, file)

usuarios = load_usuarios()
gasolina_aditivada = GasolinaAditivada()

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        if usuario in usuarios:
            return render_template('cadastro.html', erro="Usuário já existe. Tente outro nome de usuário.")

        usuarios[usuario] = senha
        save_usuarios(usuarios)
        return redirect(url_for('login'))
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        if usuarios.get(usuario) == senha:
            session['usuario'] = usuario 
            return redirect(url_for('menucombustivel'))
        else:
            return render_template('login.html', erro="Credenciais inválidas. Tente novamente.")
    return render_template('login.html')

@app.route('/esqueceu_senha', methods=['GET', 'POST'])
def esqueceu_senha():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        nova_senha = request.form.get('nova_senha')

        if usuario in usuarios:
            usuarios[usuario] = nova_senha
            save_usuarios(usuarios)
            return redirect(url_for('login'))
        else:
            return render_template('esqueceu_senha.html', erro="Usuário não encontrado.")
    return render_template('esqueceu_senha.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/menucombustivel')
def menucombustivel():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('menucombustivel.html')

@app.route('/abastecer', methods=['POST'])
def abastecer():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    tipo = request.form.get('tipo')
    quantidade = request.form.get('quantidade')
    combustivel = request.form.get('combustivel')

    try:
        quantidade = float(quantidade.replace(',', '.'))
    except ValueError:
        return render_template('menucombustivel.html', resultado="Quantidade inválida. Use números.")

    preco_por_litro = {
        'etanol': 3.50,
        'gasolina': 5.00,
        'diesel': 4.00,
        'gasolina aditivada': 5.80,
        'gnv': 3.00
    }

    if combustivel not in preco_por_litro:
        return render_template('menucombustivel.html', resultado="Combustível inválido. Por favor, selecione um válido.")

    if tipo == 'litros':
        if combustivel == 'gasolina aditivada':
            resultado = gasolina_aditivada.abastecer_por_litros(quantidade)
        else:
            valor_em_dinheiro = quantidade * preco_por_litro[combustivel]
            resultado = f"Você abasteceu {quantidade:.2f} litros de {combustivel}, que custaram R$ {valor_em_dinheiro:.2f}."
    elif tipo == 'dinheiro':
        if combustivel == 'gasolina aditivada':
            resultado = gasolina_aditivada.abastecer_por_valor(quantidade)
        else:
            litros = quantidade / preco_por_litro[combustivel]
            resultado = f"Você abasteceu R$ {quantidade:.2f}, o que equivale a {litros:.2f} litros de {combustivel}."
    else:
        resultado = "Tipo de abastecimento inválido."

    valor_a_pagar = quantidade * preco_por_litro[combustivel] if tipo == 'litros' else quantidade
    qr_code_data = f"Pagamento de R$ {valor_a_pagar:.2f} para {combustivel}\n19983824281"
    qr_code = pyqrcode.create(qr_code_data)
    qr_code_file = f"static/qrcodes/qrcode_{session['usuario']}.png"
    qr_code.png(qr_code_file, scale=6)

    return render_template('resultado.html', resultado=resultado, qr_code_file=f'qrcodes/qrcode_{session["usuario"]}.png')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return render_template('logout.html')

if __name__ == '__main__':
    app.run(debug=True)
