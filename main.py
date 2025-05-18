from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash, check_password_hash 
from sqlalchemy import text
from datetime import date

app = Flask(__name__)
app.secret_key = 'clave_secreta_temporal_mejorar_en_produccion'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Conexión a MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Gignac10#@localhost/biblioteca'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de usuario
class Usuario(db.Model):
    __tablename__ = 'Usuario'
    idUsuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.BigInteger, nullable=False)
    multasPendientes = db.Column(db.Integer)
    limitePrestamos = db.Column(db.Integer)
    
#Modelo Autor
class Autor(db.Model):
    idAutor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    descripcion = db.Column(db.String(100))

#Modelo Genero
class Genero(db.Model):
    idGenero = db.Column(db.Integer, primary_key=True)
    nombreGenero = db.Column(db.String(100))
    descripcion = db.Column(db.String(100))

#Modelo libro
class Libro(db.Model):
    isbn = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200))
    idAutor = db.Column(db.Integer, db.ForeignKey('autor.idAutor'))
    idGenero = db.Column(db.Integer, db.ForeignKey('genero.idGenero'))
    editorial = db.Column(db.String(100))
    estado = db.Column(db.String(100))
    disponibilidad = db.Column(db.String(100))
    imagen = db.Column(db.String(255), nullable=True)

#relaciones
    autor = db.relationship('Autor', backref=db.backref('libros', lazy=True))
    genero = db.relationship('Genero', backref=db.backref('libros', lazy=True))

# Modelo de préstamo
class Prestamo(db.Model):
    idPrestamo = db.Column(db.Integer, primary_key=True)
    idUsuario = db.Column(db.Integer, db.ForeignKey('Usuario.idUsuario'))
    isbn = db.Column(db.Integer, db.ForeignKey('libro.isbn'))
    fecha_prestamo = db.Column(db.Date)
    fecha_devolucion = db.Column(db.Date, nullable=True)

    usuario = db.relationship('Usuario', backref=db.backref('prestamos', lazy=True))
    libro = db.relationship('Libro', backref=db.backref('prestamos', lazy=True))

# Modelo de reserva
class Reserva(db.Model):
    idReserva = db.Column(db.Integer, primary_key=True)
    idUsuario = db.Column(db.Integer, db.ForeignKey('Usuario.idUsuario'))
    isbn = db.Column(db.Integer, db.ForeignKey('libro.isbn'))
    fecha_reserva = db.Column(db.Date)

    usuario = db.relationship('Usuario', backref=db.backref('reservas', lazy=True))
    libro = db.relationship('Libro', backref=db.backref('reservas', lazy=True))



# Ruta principal
@app.route('/')
def index():
    libros = Libro.query.all()  # Obtener todos los libros
    return render_template('index.html', libros=libros)

#Ruta ser miembro
@app.route('/start')
def start():
    return render_template('start.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        contraseña = request.form['contraseña']

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.contraseña, contraseña):
            session['username'] = usuario.nombre
            flash('Has iniciado sesión correctamente', 'success')
            return redirect(url_for('index'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')

    return render_template('login.html')

# Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        contraseña = request.form['contraseña']
        telefono = request.form['telefono']

        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('El correo ya está registrado', 'danger')
        else:
            nuevo_usuario = Usuario(
                nombre=nombre,
                email=email,
                contraseña=generate_password_hash(contraseña),
                telefono=telefono,
                multasPendientes=0,
                limitePrestamos=3
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Registro exitoso. Ahora puedes iniciar sesión', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('login'))

#Ver Detalles libro
@app.route('/libro/<string:id>')
def detalles_libro(id):
    libro = Libro.query.filter_by(isbn=id).first_or_404()
    return render_template('detalle_libro.html', libro=libro)

#busqueda 
@app.route('/buscar')
def buscar_libros():
    termino = request.args.get('q', '').strip()

    if not termino:
        return redirect(url_for('index'))

    sql = text("""
        SELECT l.*, a.nombre AS autor, g.nombreGenero AS genero
        FROM Libro l
        JOIN Autor a ON l.idAutor = a.idAutor
        JOIN Genero g ON l.idGenero = g.idGenero
        WHERE l.titulo LIKE :t
        OR a.nombre LIKE :t
        OR g.nombreGenero LIKE :t
        OR l.editorial LIKE :t
    """)

    resultados = db.session.execute(sql, {'t': f'%{termino}%'}).fetchall()

    return render_template('resultados.html', libros=resultados, termino=termino)

#Ruta para ver el historial de prestamos
@app.route('/historial')
def historial():
    if 'username' not in session:
        flash('Debes iniciar sesión para ver tu historial de préstamos', 'danger')
        return redirect(url_for('login'))

    usuario = Usuario.query.filter_by(nombre=session['username']).first()
    prestamos = Prestamo.query.filter_by(idUsuario=usuario.idUsuario).all()
    reservas = Reserva.query.filter_by(idUsuario=usuario.idUsuario).all()

    return render_template('historial.html', prestamos=prestamos, reservas=reservas)


#filtros
@app.route('/autor/<int:idAutor>')
def libros_por_autor(idAutor):
    libros = Libro.query.filter_by(idAutor=idAutor).all()
    autor = Autor.query.get(idAutor)  
    return render_template('resultados.html', libros=libros, termino=autor.nombre)

@app.route('/genero/<int:genero_id>')
def libros_por_genero(genero_id):
    libros = Libro.query.filter_by(idGenero=genero_id).all()
    genero = Genero.query.get(genero_id)  
    return render_template('resultados.html', libros=libros, termino=genero.nombreGenero)

@app.route('/reservar/<int:isbn>', methods=['POST'])
def reservar_libro(isbn):
    if 'username' not in session:
        flash('Debes iniciar sesión para reservar un libro', 'danger')
        return redirect(url_for('login'))

    usuario = Usuario.query.filter_by(nombre=session['username']).first()
    libro = Libro.query.get_or_404(isbn)

    if libro.disponibilidad != 'disponible':
        flash('El libro no está disponible para reserva', 'warning')
        return redirect(url_for('detalles_libro', id=isbn))

    reserva = Reserva(
        idUsuario=usuario.idUsuario,
        isbn=libro.isbn,
        fecha_reserva=date.today()
    )
    db.session.add(reserva)
    db.session.commit()
    flash('Libro reservado exitosamente', 'success')
    return redirect(url_for('historial'))

@app.route('/prestamo/<int:isbn>', methods=['POST'])
def prestar_libro(isbn):
    if 'username' not in session:
        flash('Debes iniciar sesión para pedir prestado un libro', 'danger')
        return redirect(url_for('login'))

    usuario = Usuario.query.filter_by(nombre=session['username']).first()
    libro = Libro.query.get_or_404(isbn)

    if libro.disponibilidad != 'disponible':
        flash('El libro no está disponible para préstamo', 'warning')
        return redirect(url_for('detalles_libro', id=isbn))

    prestamo = Prestamo(
        idUsuario=usuario.idUsuario,
        isbn=libro.isbn,
        fecha_prestamo=date.today(),
        fecha_devolucion=None
    )
    libro.disponibilidad = 'no disponible'  # marcar como prestado
    db.session.add(prestamo)
    db.session.commit()
    flash('Libro prestado exitosamente', 'success')
    return redirect(url_for('historial'))

@app.context_processor
def inject_filters():
    autores = Autor.query.all()
    generos = Genero.query.all()
    return dict(autores=autores, generos=generos)

if __name__ == '__main__':
    app.run(debug=True)
  