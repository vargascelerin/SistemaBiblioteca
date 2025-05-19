from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.security import generate_password_hash, check_password_hash 
from sqlalchemy import text
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta  # Opcional para manipulaciones más complejas

app = Flask(__name__)
app.secret_key = 'clave_secreta_temporal_mejorar_en_produccion'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Conexión a MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:21151018@localhost/biblioteca'
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

class Bibliotecario(db.Model):
    __tablename__ = 'Bibliotecario'
    idBibliotecario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(200), nullable=False)
    nivel_acceso = db.Column(db.Integer, default=1)  # 1=normal, 2=admin
    
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
    fecha_prestamo = db.Column(db.Date, default=date.today)
    fecha_devolucion_esperada = db.Column(db.Date, default=lambda: date.today() + timedelta(days=7))  # 1 semana por defecto
    fecha_devolucion_real = db.Column(db.Date, nullable=True)
    estado = db.Column(db.String(20), default='activo')  # activo, extendido, completado, vencido
    extensiones = db.Column(db.Integer, default=0)

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

@app.route('/login_bibliotecario', methods=['GET', 'POST'])
def login_bibliotecario():
    if request.method == 'POST':
        email = request.form['email']
        contraseña_plana = request.form['contraseña']

        print(f"Intento de login con: {email} y {contraseña_plana}")  # Para depuración
        
        bibliotecario = Bibliotecario.query.filter_by(email=email).first()
        
        if bibliotecario:
            # Comparación directa (sin hashing - SOLO PARA PRUEBAS)
            if bibliotecario.contraseña == contraseña_plana:
                session['bibliotecario'] = bibliotecario.nombre
                session['nivel_acceso'] = bibliotecario.nivel_acceso
                flash('Acceso concedido como bibliotecario', 'success')
                return redirect(url_for('panel_bibliotecario'))
            else:
                flash('Contraseña incorrecta', 'danger')
        else:
            flash('No existe un bibliotecario con ese email', 'danger')

    return render_template('login_bibliotecario.html')

# Panel del bibliotecario
@app.route('/panel_bibliotecario')
def panel_bibliotecario():
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    libros = Libro.query.all()
    prestamos_activos = Prestamo.query.filter_by(fecha_devolucion_real=None).count()
    reservas_pendientes = Reserva.query.count()
    
    return render_template('panel_bibliotecario.html',
                         libros=libros,
                         prestamos_activos=prestamos_activos,
                         reservas_pendientes=reservas_pendientes)

@app.route('/logout_bibliotecario')
def logout_bibliotecario():
    session.pop('bibliotecario', None)
    session.pop('nivel_acceso', None)
    flash('Has cerrado sesión como bibliotecario', 'success')
    return redirect(url_for('index'))

# Ruta para registrar nuevo libro
@app.route('/registrar_libro', methods=['GET', 'POST'])
def registrar_libro():
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    if request.method == 'POST':
        # Procesar formulario
        titulo = request.form['titulo']
        isbn = request.form['isbn']
        idAutor = request.form['autor']
        idGenero = request.form['genero']
        editorial = request.form['editorial']
        imagen = request.form.get('imagen', '')  # Opcional
        
        nuevo_libro = Libro(
            isbn=isbn,
            titulo=titulo,
            idAutor=idAutor,
            idGenero=idGenero,
            editorial=editorial,
            estado='Nuevo',
            disponibilidad='disponible',
            imagen=imagen if imagen else None
        )
        
        db.session.add(nuevo_libro)
        db.session.commit()
        flash('Libro registrado exitosamente', 'success')
        return redirect(url_for('panel_bibliotecario'))
    
    autores = Autor.query.all()
    generos = Genero.query.all()
    return render_template('registrar_libro.html', autores=autores, generos=generos)

# Ruta para registrar nuevo autor
@app.route('/registrar_autor', methods=['GET', 'POST'])
def registrar_autor():
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        
        nuevo_autor = Autor(
            nombre=nombre,
            descripcion=descripcion
        )
        
        db.session.add(nuevo_autor)
        db.session.commit()
        flash('Autor registrado exitosamente', 'success')
        return redirect(url_for('panel_bibliotecario'))
    
    return render_template('registrar_autor.html')

# Ruta para registrar nueva categoría (género)
@app.route('/registrar_genero', methods=['GET', 'POST'])
def registrar_genero():
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        
        nuevo_genero = Genero(
            nombreGenero=nombre,
            descripcion=descripcion
        )
        
        db.session.add(nuevo_genero)
        db.session.commit()
        flash('Género registrado exitosamente', 'success')
        return redirect(url_for('panel_bibliotecario'))
    
    return render_template('registrar_genero.html')

# --- Rutas para Libros ---
@app.route('/modificar_libros')
def modificar_libros():
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    libros = Libro.query.all()
    return render_template('modificar_libros.html', libros=libros)

@app.route('/editar_libro/<int:id>', methods=['GET', 'POST'])
def editar_libro(id):
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    libro = Libro.query.get_or_404(id)
    
    if request.method == 'POST':
        libro.titulo = request.form['titulo']
        libro.idAutor = request.form['autor']
        libro.idGenero = request.form['genero']
        libro.editorial = request.form['editorial']
        libro.estado = request.form['estado']
        libro.disponibilidad = request.form['disponibilidad']
        libro.imagen = request.form.get('imagen', '')
        
        db.session.commit()
        flash('Libro actualizado correctamente', 'success')
        return redirect(url_for('modificar_libros'))
    
    autores = Autor.query.all()
    generos = Genero.query.all()
    return render_template('editar_libro.html', libro=libro, autores=autores, generos=generos)

@app.route('/eliminar_libro/<int:id>', methods=['POST'])
def eliminar_libro(id):
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    libro = Libro.query.get_or_404(id)
    db.session.delete(libro)
    db.session.commit()
    flash('Libro eliminado correctamente', 'success')
    return redirect(url_for('modificar_libros'))

# --- Rutas para Autores ---
@app.route('/modificar_autores')
def modificar_autores():
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    autores = Autor.query.all()
    return render_template('modificar_autores.html', autores=autores)

@app.route('/editar_autor/<int:id>', methods=['GET', 'POST'])
def editar_autor(id):
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    autor = Autor.query.get_or_404(id)
    
    if request.method == 'POST':
        autor.nombre = request.form['nombre']
        autor.descripcion = request.form['descripcion']
        db.session.commit()
        flash('Autor actualizado correctamente', 'success')
        return redirect(url_for('modificar_autores'))
    
    return render_template('editar_autor.html', autor=autor)

@app.route('/eliminar_autor/<int:id>', methods=['POST'])
def eliminar_autor(id):
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    autor = Autor.query.get_or_404(id)
    db.session.delete(autor)
    db.session.commit()
    flash('Autor eliminado correctamente', 'success')
    return redirect(url_for('modificar_autores'))

# --- Rutas para Géneros ---
@app.route('/modificar_generos')
def modificar_generos():
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    generos = Genero.query.all()
    return render_template('modificar_generos.html', generos=generos)

@app.route('/editar_genero/<int:id>', methods=['GET', 'POST'])
def editar_genero(id):
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    genero = Genero.query.get_or_404(id)
    
    if request.method == 'POST':
        genero.nombreGenero = request.form['nombre']
        genero.descripcion = request.form['descripcion']
        db.session.commit()
        flash('Género actualizado correctamente', 'success')
        return redirect(url_for('modificar_generos'))
    
    return render_template('editar_genero.html', genero=genero)

@app.route('/eliminar_genero/<int:id>', methods=['POST'])
def eliminar_genero(id):
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    genero = Genero.query.get_or_404(id)
    db.session.delete(genero)
    db.session.commit()
    flash('Género eliminado correctamente', 'success')
    return redirect(url_for('modificar_generos'))

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

# Ruta para ver todos los préstamos (solo bibliotecario)
@app.route('/gestion_prestamos')
def gestion_prestamos():
    if 'bibliotecario' not in session:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('login_bibliotecario'))
    
    prestamos = Prestamo.query.order_by(Prestamo.fecha_devolucion_esperada).all()
    return render_template('gestion_prestamos.html', prestamos=prestamos)

# Ruta para extender un préstamo
@app.route('/extender_prestamo/<int:id>', methods=['POST'])
def extender_prestamo(id):
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    prestamo = Prestamo.query.get_or_404(id)
    
    if prestamo.extensiones >= 2:  # Límite de 2 extensiones
        flash('No se pueden hacer más extensiones', 'warning')
    else:
        prestamo.fecha_devolucion_esperada += timedelta(days=7)
        prestamo.extensiones += 1
        prestamo.estado = 'extendido'
        db.session.commit()
        flash('Préstamo extendido por 7 días más', 'success')
    
    return redirect(url_for('gestion_prestamos'))

# Ruta para registrar devolución
@app.route('/registrar_devolucion/<int:id>', methods=['POST'])
def registrar_devolucion(id):
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    prestamo = Prestamo.query.get_or_404(id)
    libro = Libro.query.get(prestamo.isbn)
    
    prestamo.fecha_devolucion_real = date.today()
    prestamo.estado = 'completado'
    libro.disponibilidad = 'disponible'
    
    db.session.commit()
    flash('Devolución registrada exitosamente', 'success')
    return redirect(url_for('gestion_prestamos'))

# Ruta para modificar fechas manualmente
@app.route('/modificar_prestamo/<int:id>', methods=['GET', 'POST'])
def modificar_prestamo(id):
    if 'bibliotecario' not in session:
        return redirect(url_for('login_bibliotecario'))
    
    prestamo = Prestamo.query.get_or_404(id)
    
    if request.method == 'POST':
        nueva_fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
        
        if request.form['tipo_fecha'] == 'prestamo':
            prestamo.fecha_prestamo = nueva_fecha
        else:
            prestamo.fecha_devolucion_esperada = nueva_fecha
        
        db.session.commit()
        flash('Fecha actualizada correctamente', 'success')
        return redirect(url_for('gestion_prestamos'))
    
    return render_template('modificar_prestamo.html', prestamo=prestamo)

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
        flash('Debes iniciar sesión', 'danger')
        return redirect(url_for('login'))

    usuario = Usuario.query.filter_by(nombre=session['username']).first()
    libro = Libro.query.get_or_404(isbn)

    # Verificar disponibilidad
    if libro.disponibilidad != 'disponible':
        flash('Libro no disponible', 'warning')
        return redirect(url_for('detalles_libro', id=isbn))
    
    # Verificar límite de préstamos (CORRECCIÓN AQUÍ)
    prestamos_activos = [p for p in usuario.prestamos if p.estado in ['activo', 'extendido']]
    if len(prestamos_activos) >= usuario.limitePrestamos:
        flash(f'Has alcanzado tu límite de {usuario.limitePrestamos} préstamos activos', 'warning')
        return redirect(url_for('detalles_libro', id=isbn))

    # Crear préstamo
    nuevo_prestamo = Prestamo(
        idUsuario=usuario.idUsuario,
        isbn=libro.isbn,
        fecha_prestamo=date.today(),
        fecha_devolucion_esperada=date.today() + timedelta(days=7),
        estado='activo'
    )
    
    libro.disponibilidad = 'no disponible'
    db.session.add(nuevo_prestamo)
    db.session.commit()
    
    flash(f'Préstamo registrado. Devolver antes del {nuevo_prestamo.fecha_devolucion_esperada.strftime("%d/%m/%Y")}', 'success')
    return redirect(url_for('historial'))

@app.context_processor
def inject_filters():
    # Actualización de préstamos vencidos (solo si hay cambios)
    prestamos_a_actualizar = Prestamo.query.filter(
        Prestamo.fecha_devolucion_esperada < date.today(),
        Prestamo.estado.in_(['activo', 'extendido'])
    ).with_for_update().all()  # Bloquea los registros para evitar condiciones de carrera
    
    if prestamos_a_actualizar:
        for p in prestamos_a_actualizar:
            p.estado = 'vencido'
        db.session.commit()
    
    # Mantenemos los filtros originales
    return {
        'autores': Autor.query.all(),
        'generos': Genero.query.all(),
        'prestamos_vencidos_count': len(prestamos_a_actualizar)  # Opcional: para mostrar notificaciones
    }
if __name__ == '__main__':
    app.run(debug=True)
  