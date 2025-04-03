from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'clave_secreta_temporal_mejorar_en_produccion'
app.config['TEMPLATES_AUTO_RELOAD'] = True


usuarios = {
    'admin': {'password': 'admin123', 'nombre': 'Administrador'},
    'usuario1': {'password': 'user123', 'nombre': 'Juan Pérez'}
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in usuarios and usuarios[username]['password'] == password:
            session['username'] = usuarios[username]['nombre']
            flash('Has iniciado sesión correctamente', 'success')
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nombre = request.form['nombre']

        if username in usuarios:
            flash('El nombre de usuario ya existe', 'danger')
        else:
            usuarios[username] = {'password': password, 'nombre': nombre}
            flash('Registro exitoso. Ahora puedes iniciar sesión', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)