from flask_sqlalchemy import SQLAlchemy
from datetime import date
from flask_login import UserMixin

db = SQLAlchemy()


class TipoHabitacion(db.Model):
    __tablename__ = 'tipos_habitaciones'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio_por_noche_usd = db.Column(db.Numeric(10, 2), nullable=False)
    precio_por_noche_bs = db.Column(db.Numeric(10, 2), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    habitaciones = db.relationship('Habitacion', backref='tipo', lazy=True)

    def __repr__(self):
        return f'<TipoHabitacion {self.nombre}>'


class Habitacion(db.Model):
    __tablename__ = 'habitaciones'

    id = db.Column(db.Integer, primary_key=True)
    tipo_habitacion_id = db.Column(db.Integer, db.ForeignKey('tipos_habitaciones.id'), nullable=False)
    numero = db.Column(db.String(20), unique=True, nullable=False)
    piso = db.Column(db.String(10))
    estado = db.Column(db.String(20), default='disponible')  # disponible, ocupada, mantenimiento
    notas = db.Column(db.Text)

    reservaciones = db.relationship('Reservacion', backref='habitacion', lazy=True)

    def __repr__(self):
        return f'<Habitacion {self.numero}>'


class Cliente(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    documento_identidad = db.Column(db.String(50), unique=True, nullable=False)

    reservaciones = db.relationship('Reservacion', backref='cliente', lazy=True)
    ventas = db.relationship('Venta', backref='cliente', lazy=True)

    def __repr__(self):
        return f'<Cliente {self.nombre} {self.apellido}>'


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contrasena = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), default='recepcionista')  # admin, recepcionista, gerente
    activo = db.Column(db.Boolean, default=True)

    # Flask-Login
    @property
    def is_active(self):
        return self.activo

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    reservaciones = db.relationship('Reservacion', backref='usuario', lazy=True)
    ventas = db.relationship('Venta', backref='usuario', lazy=True)

    def __repr__(self):
        return f'<Usuario {self.usuario}>'


class PlanTuristico(db.Model):
    __tablename__ = 'planes_turisticos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio_usd = db.Column(db.Numeric(10, 2), nullable=False)
    precio_bs = db.Column(db.Numeric(10, 2), nullable=False)
    duracion_dias = db.Column(db.Integer)
    activo = db.Column(db.Boolean, default=True)

    detalles_venta = db.relationship('VentaDetalle', backref='plan_turistico', lazy=True)

    def __repr__(self):
        return f'<PlanTuristico {self.nombre}>'


class ProductoRestaurante(db.Model):
    __tablename__ = 'productos_restaurante'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio_unitario_usd = db.Column(db.Numeric(10, 2), nullable=False)
    precio_unitario_bs = db.Column(db.Numeric(10, 2), nullable=False)
    categoria = db.Column(db.String(50))
    activo = db.Column(db.Boolean, default=True)

    detalles_venta = db.relationship('VentaDetalle', backref='producto_restaurante', lazy=True)

    def __repr__(self):
        return f'<ProductoRestaurante {self.nombre}>'


class Tasa(db.Model):
    __tablename__ = 'tasas'

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, unique=True, nullable=False)
    tasa_bs_por_usd = db.Column(db.Numeric(10, 2), nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Tasa {self.fecha}: {self.tasa_bs_por_usd}>'


class Reservacion(db.Model):
    __tablename__ = 'reservaciones'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    habitacion_id = db.Column(db.Integer, db.ForeignKey('habitaciones.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_entrada = db.Column(db.Date, nullable=False)
    fecha_salida = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), default='confirmada')  # confirmada, check-in, check-out, cancelada
    observaciones = db.Column(db.Text)
    precio_por_noche_usd = db.Column(db.Numeric(10, 2), nullable=False)
    precio_por_noche_bs = db.Column(db.Numeric(10, 2), nullable=False)

    venta = db.relationship('Venta', backref='reservacion', uselist=False, lazy=True)

    def __repr__(self):
        return f'<Reservacion {self.id} - Hab {self.habitacion_id}>'


class Venta(db.Model):
    __tablename__ = 'ventas'

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_venta = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    tipo = db.Column(db.String(20), nullable=False)  # reservacion, restaurante, plan_turistico, mixta
    reservacion_id = db.Column(db.Integer, db.ForeignKey('reservaciones.id'), nullable=True)
    subtotal_usd = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal_bs = db.Column(db.Numeric(10, 2), nullable=False)
    impuesto_usd = db.Column(db.Numeric(10, 2), default=0.00)
    impuesto_bs = db.Column(db.Numeric(10, 2), default=0.00)
    total_usd = db.Column(db.Numeric(10, 2), nullable=False)
    total_bs = db.Column(db.Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(db.String(50))
    estado = db.Column(db.String(20), default='pagado')  # pagado, pendiente, anulado
    observaciones = db.Column(db.Text)

    detalles = db.relationship('VentaDetalle', backref='venta', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Venta {self.id} - {self.fecha_venta}>'


class VentaDetalle(db.Model):
    __tablename__ = 'ventas_detalle'

    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    producto_restaurante_id = db.Column(db.Integer, db.ForeignKey('productos_restaurante.id'), nullable=True)
    plan_turistico_id = db.Column(db.Integer, db.ForeignKey('planes_turisticos.id'), nullable=True)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio_unitario_usd = db.Column(db.Numeric(10, 2), nullable=False)
    precio_unitario_bs = db.Column(db.Numeric(10, 2), nullable=False)
    total_usd = db.Column(db.Numeric(10, 2), nullable=False)
    total_bs = db.Column(db.Numeric(10, 2), nullable=False)
    descripcion = db.Column(db.Text)  # por si el nombre cambia

    # Para mantener la integridad: solo uno de los dos debe ser no nulo.
    # Esta validación se puede hacer a nivel de base de datos con un CHECK,
    # pero en SQLAlchemy se maneja mejor en la lógica de la aplicación.
    __table_args__ = (
        db.CheckConstraint(
            '(producto_restaurante_id IS NOT NULL AND plan_turistico_id IS NULL) OR '
            '(producto_restaurante_id IS NULL AND plan_turistico_id IS NOT NULL)',
            name='check_solo_un_producto'
        ),
    )

    def __repr__(self):
        return f'<VentaDetalle {self.id} - Venta {self.venta_id}>'