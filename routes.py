from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from decimal import Decimal
from models import (
    db,
    Usuario,
    TipoHabitacion,
    Habitacion,
    Cliente,
    PlanTuristico,
    ProductoRestaurante,
    Tasa,
    Reservacion,
    Venta,
    VentaDetalle,
)

# Blueprints
auth = Blueprint('auth', __name__)
main = Blueprint('main', __name__)
api = Blueprint('api', __name__, url_prefix='/api')


def _obtener_tasa_actual():
    """Devuelve la tasa de cambio activa más reciente."""
    return (
        Tasa.query.filter_by(activo=True)
        .order_by(Tasa.fecha.desc(), Tasa.id.desc())
        .first()
    )


def _to_decimal(value):
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")

# ---------- Autenticación ----------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('usuario', '').strip()
        password = request.form.get('contrasena', '')

        if not username or not password:
            flash('Por favor, complete todos los campos.', 'warning')
            return render_template('login.html')

        # Buscar usuario por su nombre de usuario (campo "usuario")
        usuario = Usuario.query.filter_by(usuario=username).first()

        if usuario and check_password_hash(usuario.contrasena, password):
            # Verificar si la cuenta está activa
            if usuario.activo:
                login_user(usuario, remember=True)
                flash(f'¡Bienvenido, {usuario.nombre}!', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                flash('Cuenta inactiva. Contacte al administrador.', 'danger')
        else:
            flash('Credenciales incorrectas. Intente nuevamente.', 'danger')

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ha cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.login'))

# ---------- Dashboard (inicio) ----------
@main.route('/dashboard')
@login_required
def dashboard():
    """Página principal después del login, accesible para todos los roles"""
    # Puedes pasar información básica del usuario al template
    return render_template('dashboard.html', usuario=current_user)

# ---------- User loader para Flask-Login ----------
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# ---------- CRUD TipoHabitacion ----------
@main.route('/tipos-habitacion')
@login_required
def lista_tipos_habitacion():
    tipos = TipoHabitacion.query.all()
    return render_template('tipos_habitacion/lista.html', tipos=tipos)


@main.route('/tipos-habitacion/nuevo', methods=['GET', 'POST'])
@login_required
def crear_tipo_habitacion():
    tasa_actual = _obtener_tasa_actual()

    if request.method == 'POST':
        if not tasa_actual:
            flash('No hay una tasa de cambio activa. Registre una antes de continuar.', 'danger')
            return redirect(url_for('main.lista_tasas'))

        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio_por_noche_usd = _to_decimal(request.form.get('precio_por_noche_usd') or 0)
        precio_por_noche_bs = precio_por_noche_usd * _to_decimal(tasa_actual.tasa_bs_por_usd)
        activo = bool(request.form.get('activo', True))

        nuevo = TipoHabitacion(
            nombre=nombre,
            descripcion=descripcion,
            precio_por_noche_usd=precio_por_noche_usd,
            precio_por_noche_bs=precio_por_noche_bs,
            activo=activo,
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Tipo de habitación creado correctamente.', 'success')
        return redirect(url_for('main.lista_tipos_habitacion'))

    return render_template('tipos_habitacion/form.html', tasa_actual=tasa_actual)


@main.route('/tipos-habitacion/<int:tipo_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tipo_habitacion(tipo_id):
    tipo = TipoHabitacion.query.get_or_404(tipo_id)
    tasa_actual = _obtener_tasa_actual()

    if request.method == 'POST':
        if not tasa_actual:
            flash('No hay una tasa de cambio activa. Registre una antes de continuar.', 'danger')
            return redirect(url_for('main.lista_tasas'))

        tipo.nombre = request.form.get('nombre')
        tipo.descripcion = request.form.get('descripcion')
        tipo.precio_por_noche_usd = _to_decimal(request.form.get('precio_por_noche_usd') or 0)
        tipo.precio_por_noche_bs = tipo.precio_por_noche_usd * _to_decimal(tasa_actual.tasa_bs_por_usd)
        tipo.activo = bool(request.form.get('activo', True))

        db.session.commit()
        flash('Tipo de habitación actualizado correctamente.', 'success')
        return redirect(url_for('main.lista_tipos_habitacion'))

    return render_template('tipos_habitacion/form.html', tipo=tipo, tasa_actual=tasa_actual)


@main.route('/tipos-habitacion/<int:tipo_id>/eliminar', methods=['POST'])
@login_required
def eliminar_tipo_habitacion(tipo_id):
    tipo = TipoHabitacion.query.get_or_404(tipo_id)
    db.session.delete(tipo)
    db.session.commit()
    flash('Tipo de habitación eliminado correctamente.', 'success')
    return redirect(url_for('main.lista_tipos_habitacion'))


# ---------- CRUD Habitacion ----------
@main.route('/habitaciones')
@login_required
def lista_habitaciones():
    habitaciones = Habitacion.query.all()
    tipos = TipoHabitacion.query.all()
    return render_template('habitaciones/lista.html', habitaciones=habitaciones, tipos=tipos)


@main.route('/habitaciones/nueva', methods=['GET', 'POST'])
@login_required
def crear_habitacion():
    tipos = TipoHabitacion.query.all()

    if request.method == 'POST':
        numero = request.form.get('numero')
        piso = request.form.get('piso')
        estado = request.form.get('estado', 'disponible')
        notas = request.form.get('notas')
        tipo_habitacion_id = request.form.get('tipo_habitacion_id')

        nueva = Habitacion(
            numero=numero,
            piso=piso,
            estado=estado,
            notas=notas,
            tipo_habitacion_id=tipo_habitacion_id,
        )
        db.session.add(nueva)
        db.session.commit()
        flash('Habitación creada correctamente.', 'success')
        return redirect(url_for('main.lista_habitaciones'))

    return render_template('habitaciones/form.html', tipos=tipos)


@main.route('/habitaciones/<int:habitacion_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_habitacion(habitacion_id):
    habitacion = Habitacion.query.get_or_404(habitacion_id)
    tipos = TipoHabitacion.query.all()

    if request.method == 'POST':
        habitacion.numero = request.form.get('numero')
        habitacion.piso = request.form.get('piso')
        habitacion.estado = request.form.get('estado', 'disponible')
        habitacion.notas = request.form.get('notas')
        habitacion.tipo_habitacion_id = request.form.get('tipo_habitacion_id')

        db.session.commit()
        flash('Habitación actualizada correctamente.', 'success')
        return redirect(url_for('main.lista_habitaciones'))

    return render_template('habitaciones/form.html', habitacion=habitacion, tipos=tipos)


@main.route('/habitaciones/<int:habitacion_id>/eliminar', methods=['POST'])
@login_required
def eliminar_habitacion(habitacion_id):
    habitacion = Habitacion.query.get_or_404(habitacion_id)
    db.session.delete(habitacion)
    db.session.commit()
    flash('Habitación eliminada correctamente.', 'success')
    return redirect(url_for('main.lista_habitaciones'))


# ---------- CRUD Cliente ----------
@main.route('/clientes')
@login_required
def lista_clientes():
    clientes = Cliente.query.all()
    return render_template('clientes/lista.html', clientes=clientes)


@main.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def crear_cliente():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        documento_identidad = request.form.get('documento_identidad')

        nuevo = Cliente(
            nombre=nombre,
            apellido=apellido,
            email=email,
            telefono=telefono,
            direccion=direccion,
            documento_identidad=documento_identidad,
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Cliente creado correctamente.', 'success')
        return redirect(url_for('main.lista_clientes'))

    return render_template('clientes/form.html')


@main.route('/clientes/<int:cliente_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == 'POST':
        cliente.nombre = request.form.get('nombre')
        cliente.apellido = request.form.get('apellido')
        cliente.email = request.form.get('email')
        cliente.telefono = request.form.get('telefono')
        cliente.direccion = request.form.get('direccion')
        cliente.documento_identidad = request.form.get('documento_identidad')

        db.session.commit()
        flash('Cliente actualizado correctamente.', 'success')
        return redirect(url_for('main.lista_clientes'))

    return render_template('clientes/form.html', cliente=cliente)


@main.route('/clientes/<int:cliente_id>/eliminar', methods=['POST'])
@login_required
def eliminar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente eliminado correctamente.', 'success')
    return redirect(url_for('main.lista_clientes'))


# ---------- CRUD PlanTuristico ----------
@main.route('/planes-turisticos')
@login_required
def lista_planes_turisticos():
    planes = PlanTuristico.query.all()
    return render_template('planes_turisticos/lista.html', planes=planes)


@main.route('/planes-turisticos/nuevo', methods=['GET', 'POST'])
@login_required
def crear_plan_turistico():
    tasa_actual = _obtener_tasa_actual()

    if request.method == 'POST':
        if not tasa_actual:
            flash('No hay una tasa de cambio activa. Registre una antes de continuar.', 'danger')
            return redirect(url_for('main.lista_tasas'))

        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio_usd = _to_decimal(request.form.get('precio_usd') or 0)
        precio_bs = precio_usd * _to_decimal(tasa_actual.tasa_bs_por_usd)
        duracion_dias = request.form.get('duracion_dias') or None
        activo = bool(request.form.get('activo', True))

        nuevo = PlanTuristico(
            nombre=nombre,
            descripcion=descripcion,
            precio_usd=precio_usd,
            precio_bs=precio_bs,
            duracion_dias=duracion_dias,
            activo=activo,
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Plan turístico creado correctamente.', 'success')
        return redirect(url_for('main.lista_planes_turisticos'))

    return render_template('planes_turisticos/form.html', tasa_actual=tasa_actual)


@main.route('/planes-turisticos/<int:plan_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_plan_turistico(plan_id):
    plan = PlanTuristico.query.get_or_404(plan_id)
    tasa_actual = _obtener_tasa_actual()

    if request.method == 'POST':
        if not tasa_actual:
            flash('No hay una tasa de cambio activa. Registre una antes de continuar.', 'danger')
            return redirect(url_for('main.lista_tasas'))

        plan.nombre = request.form.get('nombre')
        plan.descripcion = request.form.get('descripcion')
        plan.precio_usd = _to_decimal(request.form.get('precio_usd') or 0)
        plan.precio_bs = plan.precio_usd * _to_decimal(tasa_actual.tasa_bs_por_usd)
        plan.duracion_dias = request.form.get('duracion_dias') or None
        plan.activo = bool(request.form.get('activo', True))

        db.session.commit()
        flash('Plan turístico actualizado correctamente.', 'success')
        return redirect(url_for('main.lista_planes_turisticos'))

    return render_template('planes_turisticos/form.html', plan=plan, tasa_actual=tasa_actual)


@main.route('/planes-turisticos/<int:plan_id>/eliminar', methods=['POST'])
@login_required
def eliminar_plan_turistico(plan_id):
    plan = PlanTuristico.query.get_or_404(plan_id)
    db.session.delete(plan)
    db.session.commit()
    flash('Plan turístico eliminado correctamente.', 'success')
    return redirect(url_for('main.lista_planes_turisticos'))


# ---------- CRUD ProductoRestaurante ----------
@main.route('/productos-restaurante')
@login_required
def lista_productos_restaurante():
    productos = ProductoRestaurante.query.all()
    return render_template('productos_restaurante/lista.html', productos=productos)


@main.route('/productos-restaurante/nuevo', methods=['GET', 'POST'])
@login_required
def crear_producto_restaurante():
    tasa_actual = _obtener_tasa_actual()

    if request.method == 'POST':
        if not tasa_actual:
            flash('No hay una tasa de cambio activa. Registre una antes de continuar.', 'danger')
            return redirect(url_for('main.lista_tasas'))

        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio_unitario_usd = _to_decimal(request.form.get('precio_unitario_usd') or 0)
        precio_unitario_bs = precio_unitario_usd * _to_decimal(tasa_actual.tasa_bs_por_usd)
        categoria = request.form.get('categoria')
        activo = bool(request.form.get('activo', True))

        nuevo = ProductoRestaurante(
            nombre=nombre,
            descripcion=descripcion,
            precio_unitario_usd=precio_unitario_usd,
            precio_unitario_bs=precio_unitario_bs,
            categoria=categoria,
            activo=activo,
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Producto de restaurante creado correctamente.', 'success')
        return redirect(url_for('main.lista_productos_restaurante'))

    return render_template('productos_restaurante/form.html', tasa_actual=tasa_actual)


@main.route('/productos-restaurante/<int:producto_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_producto_restaurante(producto_id):
    producto = ProductoRestaurante.query.get_or_404(producto_id)
    tasa_actual = _obtener_tasa_actual()

    if request.method == 'POST':
        if not tasa_actual:
            flash('No hay una tasa de cambio activa. Registre una antes de continuar.', 'danger')
            return redirect(url_for('main.lista_tasas'))

        producto.nombre = request.form.get('nombre')
        producto.descripcion = request.form.get('descripcion')
        producto.precio_unitario_usd = _to_decimal(request.form.get('precio_unitario_usd') or 0)
        producto.precio_unitario_bs = producto.precio_unitario_usd * _to_decimal(tasa_actual.tasa_bs_por_usd)
        producto.categoria = request.form.get('categoria')
        producto.activo = bool(request.form.get('activo', True))

        db.session.commit()
        flash('Producto de restaurante actualizado correctamente.', 'success')
        return redirect(url_for('main.lista_productos_restaurante'))

    return render_template('productos_restaurante/form.html', producto=producto, tasa_actual=tasa_actual)


@main.route('/productos-restaurante/<int:producto_id>/eliminar', methods=['POST'])
@login_required
def eliminar_producto_restaurante(producto_id):
    producto = ProductoRestaurante.query.get_or_404(producto_id)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto de restaurante eliminado correctamente.', 'success')
    return redirect(url_for('main.lista_productos_restaurante'))


# ---------- CRUD Tasa ----------
@main.route('/tasas')
@login_required
def lista_tasas():
    tasas = Tasa.query.order_by(Tasa.fecha.desc()).all()
    tasa_actual = _obtener_tasa_actual()
    return render_template('tasas/lista.html', tasas=tasas, tasa_actual=tasa_actual)


@main.route('/tasas/nueva', methods=['GET', 'POST'])
@login_required
def crear_tasa():
    if request.method == 'POST':
        fecha = request.form.get('fecha')
        tasa_bs_por_usd = request.form.get('tasa_bs_por_usd') or 0
        activo = bool(request.form.get('activo', True))

        nueva = Tasa(
            fecha=fecha,
            tasa_bs_por_usd=tasa_bs_por_usd,
            activo=activo,
        )
        db.session.add(nueva)
        db.session.commit()
        flash('Tasa creada correctamente.', 'success')
        return redirect(url_for('main.lista_tasas'))

    return render_template('tasas/form.html')


@main.route('/tasas/<int:tasa_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tasa(tasa_id):
    tasa = Tasa.query.get_or_404(tasa_id)

    if request.method == 'POST':
        tasa.fecha = request.form.get('fecha')
        tasa.tasa_bs_por_usd = request.form.get('tasa_bs_por_usd') or 0
        tasa.activo = bool(request.form.get('activo', True))

        db.session.commit()
        flash('Tasa actualizada correctamente.', 'success')
        return redirect(url_for('main.lista_tasas'))

    return render_template('tasas/form.html', tasa=tasa)


@main.route('/tasas/<int:tasa_id>/eliminar', methods=['POST'])
@login_required
def eliminar_tasa(tasa_id):
    tasa = Tasa.query.get_or_404(tasa_id)
    db.session.delete(tasa)
    db.session.commit()
    flash('Tasa eliminada correctamente.', 'success')
    return redirect(url_for('main.lista_tasas'))


@main.route('/tasas/actualizar-precios', methods=['POST'])
@login_required
def actualizar_precios_con_tasa():
    """Recalcula todos los precios en Bs usando la tasa activa más reciente."""
    tasa_actual = _obtener_tasa_actual()

    if not tasa_actual:
        flash('No hay una tasa de cambio activa para actualizar precios.', 'danger')
        return redirect(url_for('main.lista_tasas'))

    tasa_valor = _to_decimal(tasa_actual.tasa_bs_por_usd)

    # Tipos de habitación
    for tipo in TipoHabitacion.query.all():
        if tipo.precio_por_noche_usd is not None:
            tipo.precio_por_noche_bs = _to_decimal(tipo.precio_por_noche_usd) * tasa_valor

    # Planes turísticos
    for plan in PlanTuristico.query.all():
        if plan.precio_usd is not None:
            plan.precio_bs = _to_decimal(plan.precio_usd) * tasa_valor

    # Productos de restaurante
    for producto in ProductoRestaurante.query.all():
        if producto.precio_unitario_usd is not None:
            producto.precio_unitario_bs = _to_decimal(producto.precio_unitario_usd) * tasa_valor

    # Reservaciones (precio por noche)
    for reservacion in Reservacion.query.all():
        if reservacion.precio_por_noche_usd is not None:
            reservacion.precio_por_noche_bs = _to_decimal(reservacion.precio_por_noche_usd) * tasa_valor

    # Ventas (subtotal / impuesto / total)
    for venta in Venta.query.all():
        if venta.subtotal_usd is not None:
            venta.subtotal_bs = _to_decimal(venta.subtotal_usd) * tasa_valor
        if venta.impuesto_usd is not None:
            venta.impuesto_bs = _to_decimal(venta.impuesto_usd) * tasa_valor
        if venta.total_usd is not None:
            venta.total_bs = _to_decimal(venta.total_usd) * tasa_valor

    # Detalles de venta (precios unitarios y totales)
    for detalle in VentaDetalle.query.all():
        if detalle.precio_unitario_usd is not None:
            detalle.precio_unitario_bs = _to_decimal(detalle.precio_unitario_usd) * tasa_valor
        if detalle.total_usd is not None:
            detalle.total_bs = _to_decimal(detalle.total_usd) * tasa_valor

    db.session.commit()
    flash('Precios en bolívares actualizados con la tasa más reciente.', 'success')
    return redirect(url_for('main.lista_tasas'))


# ---------- API: Tasas ----------
@api.route('/tasas/actual', methods=['GET'])
def api_tasa_actual():
    """Devuelve la tasa de cambio activa más reciente en formato JSON."""
    tasa = _obtener_tasa_actual()
    if not tasa:
        return jsonify({'error': 'No hay tasa activa registrada'}), 404

    return jsonify(
        {
            'id': tasa.id,
            'fecha': tasa.fecha.isoformat(),
            'tasa_bs_por_usd': str(tasa.tasa_bs_por_usd),
            'activo': tasa.activo,
        }
    )


# ---------- API: Reservaciones ----------
def _reservacion_to_dict(reservacion: Reservacion):
    return {
        'id': reservacion.id,
        'cliente_id': reservacion.cliente_id,
        'cliente_nombre': f'{reservacion.cliente.nombre} {reservacion.cliente.apellido}'
        if reservacion.cliente
        else None,
        'habitacion_id': reservacion.habitacion_id,
        'habitacion_numero': reservacion.habitacion.numero if reservacion.habitacion else None,
        'usuario_id': reservacion.usuario_id,
        'usuario_nombre': f'{reservacion.usuario.nombre} {reservacion.usuario.apellido}'
        if reservacion.usuario
        else None,
        'fecha_entrada': reservacion.fecha_entrada.isoformat() if reservacion.fecha_entrada else None,
        'fecha_salida': reservacion.fecha_salida.isoformat() if reservacion.fecha_salida else None,
        'estado': reservacion.estado,
        'observaciones': reservacion.observaciones,
        'precio_por_noche_usd': str(reservacion.precio_por_noche_usd),
        'precio_por_noche_bs': str(reservacion.precio_por_noche_bs),
    }


@api.route('/reservaciones', methods=['GET'])
def api_lista_reservaciones():
    """Lista todas las reservaciones en formato JSON."""
    reservaciones = Reservacion.query.all()
    return jsonify([_reservacion_to_dict(r) for r in reservaciones])


@api.route('/reservaciones/<int:reservacion_id>', methods=['GET'])
def api_detalle_reservacion(reservacion_id):
    """Devuelve el detalle de una reservación."""
    reservacion = Reservacion.query.get_or_404(reservacion_id)
    return jsonify(_reservacion_to_dict(reservacion))


@api.route('/reservaciones', methods=['POST'])
def api_crear_reservacion():
    """Crea una reservación desde un agente externo (por ejemplo, n8n)."""
    data = request.get_json(silent=True) or {}

    requeridos = ['cliente_id', 'habitacion_id', 'usuario_id', 'fecha_entrada', 'fecha_salida', 'precio_por_noche_usd']
    faltantes = [c for c in requeridos if c not in data]
    if faltantes:
        return jsonify({'error': f'Faltan campos requeridos: {", ".join(faltantes)}'}), 400

    tasa_actual = _obtener_tasa_actual()
    if not tasa_actual:
        return jsonify({'error': 'No hay tasa de cambio activa para calcular precios en Bs'}), 400

    try:
        precio_por_noche_usd = _to_decimal(data.get('precio_por_noche_usd'))
        precio_por_noche_bs = precio_por_noche_usd * _to_decimal(tasa_actual.tasa_bs_por_usd)

        reservacion = Reservacion(
            cliente_id=data['cliente_id'],
            habitacion_id=data['habitacion_id'],
            usuario_id=data['usuario_id'],
            fecha_entrada=data['fecha_entrada'],
            fecha_salida=data['fecha_salida'],
            estado=data.get('estado', 'confirmada'),
            observaciones=data.get('observaciones'),
            precio_por_noche_usd=precio_por_noche_usd,
            precio_por_noche_bs=precio_por_noche_bs,
        )
        db.session.add(reservacion)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'No se pudo crear la reservación', 'detalle': str(e)}), 500

    return jsonify(_reservacion_to_dict(reservacion)), 201


# ---------- API: Ventas (compras) ----------
def _venta_to_dict(venta: Venta):
    return {
        'id': venta.id,
        'cliente_id': venta.cliente_id,
        'cliente_nombre': f'{venta.cliente.nombre} {venta.cliente.apellido}'
        if venta.cliente
        else None,
        'usuario_id': venta.usuario_id,
        'usuario_nombre': f'{venta.usuario.nombre} {venta.usuario.apellido}'
        if venta.usuario
        else None,
        'tipo': venta.tipo,
        'reservacion_id': venta.reservacion_id,
        'fecha_venta': venta.fecha_venta.isoformat() if venta.fecha_venta else None,
        'subtotal_usd': str(venta.subtotal_usd),
        'subtotal_bs': str(venta.subtotal_bs),
        'impuesto_usd': str(venta.impuesto_usd),
        'impuesto_bs': str(venta.impuesto_bs),
        'total_usd': str(venta.total_usd),
        'total_bs': str(venta.total_bs),
        'metodo_pago': venta.metodo_pago,
        'estado': venta.estado,
        'observaciones': venta.observaciones,
        'detalles': [
            {
                'id': d.id,
                'producto_restaurante_id': d.producto_restaurante_id,
                'plan_turistico_id': d.plan_turistico_id,
                'cantidad': d.cantidad,
                'precio_unitario_usd': str(d.precio_unitario_usd),
                'precio_unitario_bs': str(d.precio_unitario_bs),
                'total_usd': str(d.total_usd),
                'total_bs': str(d.total_bs),
                'descripcion': d.descripcion,
            }
            for d in venta.detalles
        ],
    }


@api.route('/ventas/<int:venta_id>', methods=['GET'])
def api_detalle_venta(venta_id):
    """Devuelve el detalle de una venta/compra."""
    venta = Venta.query.get_or_404(venta_id)
    return jsonify(_venta_to_dict(venta))


@api.route('/ventas', methods=['POST'])
def api_crear_venta():
    """
    Crea una venta (compra) con sus detalles.
    JSON esperado, por ejemplo:
    {
      "cliente_id": 1,
      "usuario_id": 1,
      "tipo": "restaurante",
      "reservacion_id": null,
      "metodo_pago": "tarjeta",
      "estado": "pagado",
      "observaciones": "Opcional",
      "items": [
        {
          "producto_restaurante_id": 1,
          "plan_turistico_id": null,
          "cantidad": 2,
          "precio_unitario_usd": 10.0,
          "descripcion": "Detalle opcional"
        }
      ]
    }
    """
    data = request.get_json(silent=True) or {}

    requeridos = ['cliente_id', 'usuario_id', 'tipo', 'items']
    faltantes = [c for c in requeridos if c not in data]
    if faltantes:
        return jsonify({'error': f'Faltan campos requeridos: {", ".join(faltantes)}'}), 400

    items = data.get('items') or []
    if not isinstance(items, list) or not items:
        return jsonify({'error': 'Debe enviar al menos un item en "items".'}), 400

    tasa_actual = _obtener_tasa_actual()
    if not tasa_actual:
        return jsonify({'error': 'No hay tasa de cambio activa para calcular precios en Bs'}), 400

    tasa_valor = _to_decimal(tasa_actual.tasa_bs_por_usd)

    try:
        subtotal_usd = Decimal('0')
        detalles = []

        for item in items:
            cantidad = int(item.get('cantidad') or 1)
            precio_unitario_usd = _to_decimal(item.get('precio_unitario_usd') or 0)
            total_usd_detalle = precio_unitario_usd * cantidad

            detalle = VentaDetalle(
                producto_restaurante_id=item.get('producto_restaurante_id'),
                plan_turistico_id=item.get('plan_turistico_id'),
                cantidad=cantidad,
                precio_unitario_usd=precio_unitario_usd,
                precio_unitario_bs=precio_unitario_usd * tasa_valor,
                total_usd=total_usd_detalle,
                total_bs=total_usd_detalle * tasa_valor,
                descripcion=item.get('descripcion'),
            )
            detalles.append(detalle)
            subtotal_usd += total_usd_detalle

        impuesto_usd = _to_decimal(data.get('impuesto_usd') or 0)
        total_usd = subtotal_usd + impuesto_usd

        venta = Venta(
            cliente_id=data['cliente_id'],
            usuario_id=data['usuario_id'],
            tipo=data['tipo'],
            reservacion_id=data.get('reservacion_id'),
            subtotal_usd=subtotal_usd,
            subtotal_bs=subtotal_usd * tasa_valor,
            impuesto_usd=impuesto_usd,
            impuesto_bs=impuesto_usd * tasa_valor,
            total_usd=total_usd,
            total_bs=total_usd * tasa_valor,
            metodo_pago=data.get('metodo_pago'),
            estado=data.get('estado', 'pagado'),
            observaciones=data.get('observaciones'),
        )

        for d in detalles:
            venta.detalles.append(d)

        db.session.add(venta)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'No se pudo crear la venta', 'detalle': str(e)}), 500

    return jsonify(_venta_to_dict(venta)), 201


# ---------- CRUD Reservacion ----------
@main.route('/reservaciones')
@login_required
def lista_reservaciones():
    reservaciones = Reservacion.query.all()
    clientes = Cliente.query.all()
    habitaciones = Habitacion.query.all()
    usuarios = Usuario.query.all()
    return render_template(
        'reservaciones/lista.html',
        reservaciones=reservaciones,
        clientes=clientes,
        habitaciones=habitaciones,
        usuarios=usuarios,
    )


@main.route('/reservaciones/nueva', methods=['GET', 'POST'])
@login_required
def crear_reservacion():
    clientes = Cliente.query.all()
    habitaciones = Habitacion.query.all()
    usuarios = Usuario.query.all()
    tasa_actual = _obtener_tasa_actual()

    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        habitacion_id = request.form.get('habitacion_id')
        usuario_id = request.form.get('usuario_id')
        fecha_entrada = request.form.get('fecha_entrada')
        fecha_salida = request.form.get('fecha_salida')
        estado = request.form.get('estado', 'confirmada')
        observaciones = request.form.get('observaciones')
        if not tasa_actual:
            flash('No hay una tasa de cambio activa. Registre una antes de continuar.', 'danger')
            return redirect(url_for('main.lista_tasas'))

        precio_por_noche_usd = _to_decimal(request.form.get('precio_por_noche_usd') or 0)
        precio_por_noche_bs = precio_por_noche_usd * _to_decimal(tasa_actual.tasa_bs_por_usd)

        nueva = Reservacion(
            cliente_id=cliente_id,
            habitacion_id=habitacion_id,
            usuario_id=usuario_id,
            fecha_entrada=fecha_entrada,
            fecha_salida=fecha_salida,
            estado=estado,
            observaciones=observaciones,
            precio_por_noche_usd=precio_por_noche_usd,
            precio_por_noche_bs=precio_por_noche_bs,
        )
        db.session.add(nueva)
        db.session.commit()
        flash('Reservación creada correctamente.', 'success')
        return redirect(url_for('main.lista_reservaciones'))

    return render_template(
        'reservaciones/form.html',
        clientes=clientes,
        habitaciones=habitaciones,
        usuarios=usuarios,
        tasa_actual=tasa_actual,
    )


@main.route('/reservaciones/<int:reservacion_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_reservacion(reservacion_id):
    reservacion = Reservacion.query.get_or_404(reservacion_id)
    clientes = Cliente.query.all()
    habitaciones = Habitacion.query.all()
    usuarios = Usuario.query.all()
    tasa_actual = _obtener_tasa_actual()

    if request.method == 'POST':
        reservacion.cliente_id = request.form.get('cliente_id')
        reservacion.habitacion_id = request.form.get('habitacion_id')
        reservacion.usuario_id = request.form.get('usuario_id')
        reservacion.fecha_entrada = request.form.get('fecha_entrada')
        reservacion.fecha_salida = request.form.get('fecha_salida')
        reservacion.estado = request.form.get('estado', 'confirmada')
        reservacion.observaciones = request.form.get('observaciones')
        if not tasa_actual:
            flash('No hay una tasa de cambio activa. Registre una antes de continuar.', 'danger')
            return redirect(url_for('main.lista_tasas'))

        reservacion.precio_por_noche_usd = _to_decimal(request.form.get('precio_por_noche_usd') or 0)
        reservacion.precio_por_noche_bs = reservacion.precio_por_noche_usd * _to_decimal(tasa_actual.tasa_bs_por_usd)

        db.session.commit()
        flash('Reservación actualizada correctamente.', 'success')
        return redirect(url_for('main.lista_reservaciones'))

    return render_template(
        'reservaciones/form.html',
        reservacion=reservacion,
        clientes=clientes,
        habitaciones=habitaciones,
        usuarios=usuarios,
        tasa_actual=tasa_actual,
    )


@main.route('/reservaciones/<int:reservacion_id>/eliminar', methods=['POST'])
@login_required
def eliminar_reservacion(reservacion_id):
    reservacion = Reservacion.query.get_or_404(reservacion_id)
    db.session.delete(reservacion)
    db.session.commit()
    flash('Reservación eliminada correctamente.', 'success')
    return redirect(url_for('main.lista_reservaciones'))


# ---------- CRUD Venta ----------
@main.route('/ventas')
@login_required
def lista_ventas():
    ventas = Venta.query.all()
    clientes = Cliente.query.all()
    usuarios = Usuario.query.all()
    return render_template(
        'ventas/lista.html',
        ventas=ventas,
        clientes=clientes,
        usuarios=usuarios,
    )


@main.route('/ventas/nueva', methods=['GET', 'POST'])
@login_required
def crear_venta():
    clientes = Cliente.query.all()
    usuarios = Usuario.query.all()
    tasa_actual = _obtener_tasa_actual()

    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        usuario_id = request.form.get('usuario_id')
        tipo = request.form.get('tipo')
        reservacion_id = request.form.get('reservacion_id') or None
        if not tasa_actual:
            flash('No hay una tasa de cambio activa. Registre una antes de continuar.', 'danger')
            return redirect(url_for('main.lista_tasas'))

        subtotal_usd = _to_decimal(request.form.get('subtotal_usd') or 0)
        impuesto_usd = _to_decimal(request.form.get('impuesto_usd') or 0)
        total_usd = _to_decimal(request.form.get('total_usd') or 0)

        tasa_valor = _to_decimal(tasa_actual.tasa_bs_por_usd)
        subtotal_bs = subtotal_usd * tasa_valor
        impuesto_bs = impuesto_usd * tasa_valor
        total_bs = total_usd * tasa_valor
        metodo_pago = request.form.get('metodo_pago')
        estado = request.form.get('estado', 'pagado')
        observaciones = request.form.get('observaciones')

        nueva = Venta(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            tipo=tipo,
            reservacion_id=reservacion_id,
            subtotal_usd=subtotal_usd,
            subtotal_bs=subtotal_bs,
            impuesto_usd=impuesto_usd,
            impuesto_bs=impuesto_bs,
            total_usd=total_usd,
            total_bs=total_bs,
            metodo_pago=metodo_pago,
            estado=estado,
            observaciones=observaciones,
        )
        db.session.add(nueva)
        db.session.commit()
        flash('Venta creada correctamente.', 'success')
        return redirect(url_for('main.lista_ventas'))

    return render_template(
        'ventas/form.html',
        clientes=clientes,
        usuarios=usuarios,
        tasa_actual=tasa_actual,
    )


@main.route('/ventas/<int:venta_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_venta(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    clientes = Cliente.query.all()
    usuarios = Usuario.query.all()
    tasa_actual = _obtener_tasa_actual()

    if request.method == 'POST':
        venta.cliente_id = request.form.get('cliente_id')
        venta.usuario_id = request.form.get('usuario_id')
        venta.tipo = request.form.get('tipo')
        venta.reservacion_id = request.form.get('reservacion_id') or None
        if not tasa_actual:
            flash('No hay una tasa de cambio activa. Registre una antes de continuar.', 'danger')
            return redirect(url_for('main.lista_tasas'))

        venta.subtotal_usd = _to_decimal(request.form.get('subtotal_usd') or 0)
        venta.impuesto_usd = _to_decimal(request.form.get('impuesto_usd') or 0)
        venta.total_usd = _to_decimal(request.form.get('total_usd') or 0)

        tasa_valor = _to_decimal(tasa_actual.tasa_bs_por_usd)
        venta.subtotal_bs = venta.subtotal_usd * tasa_valor
        venta.impuesto_bs = venta.impuesto_usd * tasa_valor
        venta.total_bs = venta.total_usd * tasa_valor
        venta.metodo_pago = request.form.get('metodo_pago')
        venta.estado = request.form.get('estado', 'pagado')
        venta.observaciones = request.form.get('observaciones')

        db.session.commit()
        flash('Venta actualizada correctamente.', 'success')
        return redirect(url_for('main.lista_ventas'))

    return render_template(
        'ventas/form.html',
        venta=venta,
        clientes=clientes,
        usuarios=usuarios,
        tasa_actual=tasa_actual,
    )


@main.route('/ventas/<int:venta_id>/eliminar', methods=['POST'])
@login_required
def eliminar_venta(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    db.session.delete(venta)
    db.session.commit()
    flash('Venta eliminada correctamente.', 'success')
    return redirect(url_for('main.lista_ventas'))


# ---------- CRUD VentaDetalle ----------
@main.route('/ventas-detalle')
@login_required
def lista_ventas_detalle():
    detalles = VentaDetalle.query.all()
    ventas = Venta.query.all()
    productos = ProductoRestaurante.query.all()
    planes = PlanTuristico.query.all()
    return render_template(
        'ventas_detalle/lista.html',
        detalles=detalles,
        ventas=ventas,
        productos=productos,
        planes=planes,
    )


@main.route('/ventas-detalle/nuevo', methods=['GET', 'POST'])
@login_required
def crear_venta_detalle():
    ventas = Venta.query.all()
    productos = ProductoRestaurante.query.all()
    planes = PlanTuristico.query.all()
    tasa_actual = _obtener_tasa_actual()

    if request.method == 'POST':
        venta_id = request.form.get('venta_id')
        producto_restaurante_id = request.form.get('producto_restaurante_id') or None
        plan_turistico_id = request.form.get('plan_turistico_id') or None
        if not tasa_actual:
            flash('No hay una tasa de cambio activa. Registre una antes de continuar.', 'danger')
            return redirect(url_for('main.lista_tasas'))

        cantidad = int(request.form.get('cantidad') or 1)
        precio_unitario_usd = _to_decimal(request.form.get('precio_unitario_usd') or 0)
        total_usd = _to_decimal(request.form.get('total_usd') or 0)

        tasa_valor = _to_decimal(tasa_actual.tasa_bs_por_usd)
        precio_unitario_bs = precio_unitario_usd * tasa_valor
        total_bs = total_usd * tasa_valor
        descripcion = request.form.get('descripcion')

        nuevo = VentaDetalle(
            venta_id=venta_id,
            producto_restaurante_id=producto_restaurante_id,
            plan_turistico_id=plan_turistico_id,
            cantidad=cantidad,
            precio_unitario_usd=precio_unitario_usd,
            precio_unitario_bs=precio_unitario_bs,
            total_usd=total_usd,
            total_bs=total_bs,
            descripcion=descripcion,
        )
        db.session.add(nuevo)
        db.session.commit()
        flash('Detalle de venta creado correctamente.', 'success')
        return redirect(url_for('main.lista_ventas_detalle'))

    return render_template(
        'ventas_detalle/form.html',
        ventas=ventas,
        productos=productos,
        planes=planes,
        tasa_actual=tasa_actual,
    )


@main.route('/ventas-detalle/<int:detalle_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_venta_detalle(detalle_id):
    detalle = VentaDetalle.query.get_or_404(detalle_id)
    ventas = Venta.query.all()
    productos = ProductoRestaurante.query.all()
    planes = PlanTuristico.query.all()
    tasa_actual = _obtener_tasa_actual()

    if request.method == 'POST':
        detalle.venta_id = request.form.get('venta_id')
        detalle.producto_restaurante_id = request.form.get('producto_restaurante_id') or None
        detalle.plan_turistico_id = request.form.get('plan_turistico_id') or None
        if not tasa_actual:
            flash('No hay una tasa de cambio activa. Registre una antes de continuar.', 'danger')
            return redirect(url_for('main.lista_tasas'))

        detalle.cantidad = int(request.form.get('cantidad') or 1)
        detalle.precio_unitario_usd = _to_decimal(request.form.get('precio_unitario_usd') or 0)
        detalle.total_usd = _to_decimal(request.form.get('total_usd') or 0)

        tasa_valor = _to_decimal(tasa_actual.tasa_bs_por_usd)
        detalle.precio_unitario_bs = detalle.precio_unitario_usd * tasa_valor
        detalle.total_bs = detalle.total_usd * tasa_valor
        detalle.descripcion = request.form.get('descripcion')

        db.session.commit()
        flash('Detalle de venta actualizado correctamente.', 'success')
        return redirect(url_for('main.lista_ventas_detalle'))

    return render_template(
        'ventas_detalle/form.html',
        detalle=detalle,
        ventas=ventas,
        productos=productos,
        planes=planes,
        tasa_actual=tasa_actual,
    )


@main.route('/ventas-detalle/<int:detalle_id>/eliminar', methods=['POST'])
@login_required
def eliminar_venta_detalle(detalle_id):
    detalle = VentaDetalle.query.get_or_404(detalle_id)
    db.session.delete(detalle)
    db.session.commit()
    flash('Detalle de venta eliminado correctamente.', 'success')
    return redirect(url_for('main.lista_ventas_detalle'))