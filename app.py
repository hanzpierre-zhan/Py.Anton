import os
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import io

# Configuración de rutas absolutas
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "anton.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'anton_minimal_secret_key'
db = SQLAlchemy(app)

# --- MODELOS DE DATOS ---

class FiltroMaestro(db.Model):
    __tablename__ = 'filtros_maestros'
    id = db.Column(db.Integer, primary_key=True)
    entidad = db.Column(db.String(50), nullable=False) # 'JEFATURA', 'SUBPROYECTO', 'TECNICO', 'ESTADO'
    valor = db.Column(db.String(100), nullable=False)
    __table_args__ = (db.UniqueConstraint('entidad', 'valor', name='_entidad_valor_uc'),)

class GestionObra(db.Model):
    __tablename__ = 'gestion_obras'
    id = db.Column(db.Integer, primary_key=True)
    data_json = db.Column(db.Text, nullable=False)
    fecha_carga = db.Column(db.DateTime, default=datetime.utcnow)

class ColumnaManual(db.Model):
    __tablename__ = 'columnas_manuales'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    tipo = db.Column(db.String(20), nullable=False) # 'fecha', 'lista', 'texto'
    opciones = db.Column(db.Text, nullable=True) # Para tipo 'lista', separado por comas

class ConfiguracionFiltro(db.Model):
    __tablename__ = 'configuracion_filtros'
    id = db.Column(db.Integer, primary_key=True)
    columna = db.Column(db.String(100), unique=True, nullable=False)
    tipo = db.Column(db.String(20), default='search') # 'search' o 'list'
    virtual_cols_json = db.Column(db.Text, nullable=True, default='[]')

class FiltroVirtual(db.Model):
    __tablename__ = 'filtros_virtuales'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False) # Ej: "MERCADO", "SEGMENTO"

class MapeoFiltro(db.Model):
    __tablename__ = 'mapeos_filtros'
    id = db.Column(db.Integer, primary_key=True)
    columna_criterio = db.Column(db.String(50), nullable=False) # Ej: "JEFATURA"
    valor_criterio = db.Column(db.String(100), nullable=False) # Ej: "TUMBES"
    valores_json = db.Column(db.Text, nullable=False) # JSON: {"MERCADO": "NORTE", "ZONA": "Z1"}

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(50), nullable=False) # Ej: "Admin", "Lector"
    activo = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(256), nullable=True)
    restricciones = db.relationship('RestriccionUsuario', backref='usuario_rel', cascade='all, delete-orphan')

class RestriccionUsuario(db.Model):
    __tablename__ = 'restricciones_usuario'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    columna = db.Column(db.String(100), nullable=False)  # Ej: "JEFATURA"
    valores_json = db.Column(db.Text, nullable=False)    # Ej: '["LIMA", "NORTE"]'

# --- INICIALIZACIÓN ---

with app.app_context():
    db.create_all()

# --- HELPERS DE SESIÓN ---

from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('route_login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('route_login'))
        
        user_rol = session.get('user_rol')
        user_id = session.get('user_id')
        
        # Si no hay rol en sesión, lo buscamos en la DB (para sesiones antiguas)
        if not user_rol and user_id:
            u = db.session.get(Usuario, user_id)
            if u:
                user_rol = u.rol
                session['user_rol'] = user_rol
        
        if user_rol not in ['Admin', 'Administrador']:
            return redirect(url_for('route_proyectos'))
        return f(*args, **kwargs)
    return decorated

@app.context_processor
def inject_current_user():
    """Inyecta current_user en todos los templates."""
    user_id = session.get('user_id')
    if user_id:
        u = db.session.get(Usuario, user_id)
        if u:
            return {'current_user': {'id': u.id, 'usuario': u.usuario, 'nombres': u.nombres, 'rol': u.rol}}
    return {'current_user': None}

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/login')
def route_login():
    if 'user_id' in session:
        return redirect('/')
    error = request.args.get('error')
    return render_template('login.html', error=error)

@app.route('/logout')
def route_logout():
    session.clear()
    return redirect(url_for('route_login'))

@app.route('/')
@login_required
def route_proyectos():
    return render_template('proyectos.html')

@app.route('/importar')
@admin_required
def route_importar():
    return render_template('importar.html')

@app.route('/tablas')
@admin_required
def route_tablas():
    return render_template('tablas.html')

@app.route('/filtros')
@admin_required
def route_filtros():
    return render_template('filtros.html')

@app.route('/usuarios')
@admin_required
def route_usuarios():
    return render_template('usuarios.html')

@app.route('/dashboard')
@login_required
def route_dashboard():
    return render_template('dashboard.html')

# --- API: LOGIN ---

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = (data.get('usuario') or '').strip()
    password = (data.get('password') or '').strip()

    user = Usuario.query.filter_by(usuario=username, activo=True).first()
    if not user:
        return jsonify({'success': False, 'message': 'Usuario no encontrado o inactivo.'}), 401
    if not user.password_hash:
        return jsonify({'success': False, 'message': 'El usuario no tiene contraseña configurada. Contacte al administrador.'}), 401
    if not check_password_hash(user.password_hash, password):
        return jsonify({'success': False, 'message': 'Contraseña incorrecta.'}), 401

    session.permanent = True
    session['user_id'] = user.id
    session['user_rol'] = user.rol
    return jsonify({'success': True, 'redirect': '/'})

# --- API: USUARIOS ---

@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    users = Usuario.query.all()
    resultado = [{"id": u.id, "usuario": u.usuario, "nombres": u.nombres, "rol": u.rol, "activo": u.activo, "tiene_password": bool(u.password_hash)} for u in users]
    return jsonify(resultado)

@app.route('/api/usuarios', methods=['POST'])
def add_usuario():
    data = request.json
    try:
        nuevo = Usuario(
            usuario=data['usuario'].strip(),
            nombres=data['nombres'].strip(),
            rol=data['rol'].strip(),
            activo=data.get('activo', True)
        )
        if data.get('password'):
            nuevo.password_hash = generate_password_hash(data['password'].strip())
        db.session.add(nuevo)
        db.session.commit()
        return jsonify({"success": True, "id": nuevo.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": "Error al guardar (usuario debe ser único)."}), 400

@app.route('/api/usuarios/<int:id>', methods=['PUT', 'DELETE'])
def manage_usuario(id):
    user = db.session.get(Usuario, id)
    if not user:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
        
    if request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return jsonify({"success": True, "message": "Usuario eliminado"})
        
    if request.method == 'PUT':
        data = request.json
        if 'nombres' in data: user.nombres = data['nombres'].strip()
        if 'rol' in data: user.rol = data['rol'].strip()
        if 'activo' in data: user.activo = data['activo']
        if data.get('password'): user.password_hash = generate_password_hash(data['password'].strip())
        
        try:
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/usuarios/<int:id>/restricciones', methods=['GET'])
def get_restricciones(id):
    user = db.session.get(Usuario, id)
    if not user:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
    resultado = [{"id": r.id, "columna": r.columna, "valores": json.loads(r.valores_json)} for r in user.restricciones]
    return jsonify(resultado)

@app.route('/api/usuarios/<int:id>/restricciones', methods=['POST'])
def add_restriccion(id):
    user = db.session.get(Usuario, id)
    if not user:
        return jsonify({"success": False, "message": "Usuario no encontrado"}), 404
    data = request.json
    columna = data.get('columna', '').strip()
    valores = data.get('valores', [])
    if not columna or not valores:
        return jsonify({"success": False, "message": "Columna y valores son requeridos"}), 400
    # Si ya existe una restriccion para esa columna, añade los nuevos valores sin duplicados
    existing = next((r for r in user.restricciones if r.columna == columna), None)
    if existing:
        valores_actuales = json.loads(existing.valores_json)
        # Combinar listas y quitar duplicados
        nuevos_valores = list(set(valores_actuales + valores))
        existing.valores_json = json.dumps(nuevos_valores)
    else:
        db.session.add(RestriccionUsuario(usuario_id=id, columna=columna, valores_json=json.dumps(valores)))
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/usuarios/restricciones/<int:rid>', methods=['DELETE'])
def delete_restriccion(rid):
    r = db.session.get(RestriccionUsuario, rid)
    if not r:
        return jsonify({"success": False}), 404
    db.session.delete(r)
    db.session.commit()
    return jsonify({"success": True})

# --- API: TABLAS (FILTROS MAESTROS) ---

@app.route('/api/filtros', methods=['GET'])
def get_filtros():
    filtros = FiltroMaestro.query.all()
    resultado = {}
    for f in filtros:
        if f.entidad not in resultado:
            resultado[f.entidad] = []
        resultado[f.entidad].append({"id": f.id, "valor": f.valor})
    return jsonify(resultado)

@app.route('/api/filtros', methods=['POST'])
def add_filtro():
    data = request.json
    # Respetamos el casing del usuario para la entidad y el valor
    nuevo = FiltroMaestro(entidad=data['entidad'].strip(), valor=data['valor'].strip())
    try:
        db.session.add(nuevo)
        db.session.commit()
        return jsonify({"success": True, "id": nuevo.id})
    except:
        db.session.rollback()
        return jsonify({"success": False, "message": "Valor ya existe en esta entidad"}), 400

@app.route('/api/filtros/bulk', methods=['POST'])
def bulk_filtros():
    data = request.json # { entidad: '...', valores: [...] }
    entidad = data['entidad'].strip()
    count = 0
    for v in data['valores']:
        val = str(v).strip() # Quitamos el .upper() para respetar el formato
        if not FiltroMaestro.query.filter_by(entidad=entidad, valor=val).first():
            db.session.add(FiltroMaestro(entidad=entidad, valor=val))
            count += 1
    db.session.commit()
    return jsonify({"success": True, "added": count})

@app.route('/api/filtros/clear', methods=['POST'])
def clear_filtros():
    entidad = request.json.get('entidad')
    if entidad:
        FiltroMaestro.query.filter_by(entidad=entidad.strip()).delete()
    else:
        FiltroMaestro.query.delete()
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/filtros/<int:id>', methods=['DELETE'])
def delete_filtro(id):
    filtro = db.session.get(FiltroMaestro, id)
    if filtro:
        db.session.delete(filtro)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "No encontrado"}), 404

@app.route('/api/filtros/entidad/rename', methods=['POST'])
def rename_entidad():
    data = request.json
    vieja = data['vieja'].strip()
    nueva = data['nueva'].strip()
    filtros = FiltroMaestro.query.filter_by(entidad=vieja).all()
    for f in filtros:
        f.entidad = nueva
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/filtros/entidad/delete', methods=['POST'])
def delete_entidad():
    data = request.json
    entidad = data['entidad'].strip()
    FiltroMaestro.query.filter_by(entidad=entidad).delete()
    db.session.commit()
    return jsonify({"success": True})

# --- API: IMPORTAR ---

@app.route('/api/import', methods=['POST'])
def process_import():
    file = request.files.get('file')
    source_type = request.form.get('source_type', 'planobraCSV')
    filter_active = request.form.get('filter_active') == 'true'
    entidad_filtro = request.form.get('entidad_filtro', 'ESTADO PLAN').strip()
    
    if not file: return jsonify({"error": "No hay archivo"}), 400
    
    filename = file.filename
    if filename.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    
    # Limpieza y Normalización
    df.columns = [str(c).upper().strip() for c in df.columns]
    df = df.fillna("")
    
    # Normalizar ITEMPLAN (quitar .0 de Excel y limpiar espacios)
    if 'ITEMPLAN' in df.columns:
        df['ITEMPLAN'] = df['ITEMPLAN'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

    for col in df.columns:
        if col != 'ITEMPLAN':
            df[col] = df[col].astype(str).str.strip()

    total_rows = len(df)
    imported = 0
    updated = 0
    discarded = 0

    # Obtener todos los registros actuales para comparación rápida (por ITEMPLAN)
    # Nota: Como los datos están en JSON, necesitamos procesar un poco
    obras_actuales = GestionObra.query.all()
    cache_obras = {} # { 'ITEMPLAN': objeto_db }
    for o in obras_actuales:
        data = json.loads(o.data_json)
        itp = data.get('ITEMPLAN')
        if itp:
            cache_obras[itp] = o

    # Obtener todos los criterios de filtrado si el filtrado está activo
    filtros_dict = {} # { 'ENTIDAD': ['valor1', 'valor2'] }
    if filter_active:
        todos_los_filtros = FiltroMaestro.query.all()
        for f in todos_los_filtros:
            entidad = f.entidad.strip()
            if entidad not in filtros_dict:
                filtros_dict[entidad] = []
            filtros_dict[entidad].append(f.valor.strip())

    # Pre-cargar nombres de columnas manuales para source_type == 'manual_update'
    manual_cols_names = [c.nombre.upper().strip() for c in ColumnaManual.query.all()]

    # --- Lógica específica para Detalle Plan (Agregación MO y MAT) ---
    if source_type == 'detalleplanCSV':
        df['VALORIZ MANO DE OBRA'] = pd.to_numeric(df['VALORIZ MANO DE OBRA'], errors='coerce').fillna(0)
        
        def join_unique(series):
            parts = [str(v).strip() for v in series.unique() if v and str(v).strip().lower() not in ["", "nan", "none", "0", "0.0"]]
            return ', '.join(sorted(list(set(parts))))

        # Procesamos por ITEMPLAN
        for itp, group in df.groupby('ITEMPLAN'):
            if itp in cache_obras:
                obra_db = cache_obras[itp]
                data_actual = json.loads(obra_db.data_json)

                # 1. Lógica para Mano de Obra (MO_) -> VALORIZACIÓN
                mask_mo = pd.Series([False] * len(group), index=group.index)
                for col in ['PO', 'AREA']:
                    if col in group.columns:
                        mask_mo = mask_mo | group[col].astype(str).str.upper().str.startswith('MO_')
                
                mo_group = group[mask_mo]
                if not mo_group.empty:
                    data_actual['VALORIZ MANO DE OBRA'] = float(mo_group['VALORIZ MANO DE OBRA'].sum())

                # 2. Lógica para Materiales (MAT_) -> PO y VR
                mask_mat = pd.Series([False] * len(group), index=group.index)
                for col in ['PO', 'AREA']:
                    if col in group.columns:
                        mask_mat = mask_mat | group[col].astype(str).str.upper().str.startswith('MAT_')
                
                mat_group = group[mask_mat]
                if not mat_group.empty:
                    if 'PO' in mat_group.columns:
                        data_actual['PO'] = join_unique(mat_group['PO'])
                    if 'VR' in mat_group.columns:
                        data_actual['VR'] = join_unique(mat_group['VR'])
                
                obra_db.data_json = json.dumps(data_actual)
                updated += 1
            else:
                discarded += 1

        db.session.commit()
        return jsonify({
            "total": total_rows,
            "imported": 0,
            "updated": updated,
            "discarded": discarded,
            "source": source_type
        })
    # --- Fin Lógica Detalle Plan ---

    for _, row in df.iterrows():
        fila_dict = row.to_dict()
        fila_dict['__source'] = source_type
        
        # 1. Validar Filtrado Maestro
        should_discard = False
        if filter_active:
            for entidad, valores_permitidos in filtros_dict.items():
                if entidad in fila_dict:
                    val_actual = str(fila_dict[entidad] or "").strip()
                    if val_actual not in valores_permitidos:
                        should_discard = True
                        break
        
        if should_discard:
            discarded += 1
            continue
        
        itemplan_nuevo = fila_dict.get('ITEMPLAN')
        
        # 2. Lógica de Actualización vs Inserción
        if itemplan_nuevo in cache_obras:
            # Caso EXISTE: Solo actualizamos campos específicos (ESTADO PLAN y SUBESTADO TRUNCO)
            obra_db = cache_obras[itemplan_nuevo]
            data_actual = json.loads(obra_db.data_json)
            
            if source_type == 'manual_update':
                # Caso MANUAL: Actualizamos cualquier columna que coincida con manual_cols_names
                manual_updated = False
                for col_name, val in fila_dict.items():
                    c_upper = col_name.upper().strip()
                    if c_upper in manual_cols_names:
                        data_actual[c_upper] = str(val).strip() if val else ""
                        manual_updated = True
                
                if manual_updated:
                    obra_db.data_json = json.dumps(data_actual)
                    updated += 1
                else:
                    discarded += 1
                continue

            if 'ESTADO PLAN' in fila_dict:
                data_actual['ESTADO PLAN'] = fila_dict['ESTADO PLAN']
            if 'SUBESTADO TRUNCO' in fila_dict:
                data_actual['SUBESTADO TRUNCO'] = fila_dict['SUBESTADO TRUNCO']
            
            # Nuevos reportes: Cotización y PDT Cert
            if source_type == 'reporte_cotizacion' and 'ESTADO' in fila_dict:
                data_actual['ESTADO'] = fila_dict['ESTADO']
            if source_type == 'reporte_pdt_validar_cert' and 'SITUACION' in fila_dict:
                data_actual['SITUACION'] = fila_dict['SITUACION']
            
            obra_db.data_json = json.dumps(data_actual)
            updated += 1
        elif source_type == 'planobraCSV':
            # Caso NUEVO: SOLO si es la base principal
            nueva_obra = GestionObra(data_json=json.dumps(fila_dict))
            db.session.add(nueva_obra)
            imported += 1
        else:
            # Si no existe y NO es la base principal, se descarta (no cruza nada)
            discarded += 1

    db.session.commit()
    return jsonify({
        "total": total_rows,
        "imported": imported,
        "updated": updated,
        "discarded": discarded,
        "source": source_type
    })

# --- API: COLUMNAS MANUALES ---

@app.route('/api/config/manual-columns', methods=['GET'])
def get_manual_columns():
    cols = ColumnaManual.query.all()
    return jsonify([{
        "id": c.id,
        "nombre": c.nombre,
        "tipo": c.tipo,
        "opciones": c.opciones
    } for c in cols])

@app.route('/api/config/manual-columns', methods=['POST'])
def add_manual_column():
    data = request.json
    nueva = ColumnaManual(
        nombre=data['nombre'].strip(),
        tipo=data['tipo'],
        opciones=data.get('opciones', '')
    )
    try:
        db.session.add(nueva)
        db.session.commit()
        return jsonify({"success": True, "id": nueva.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/config/manual-columns/<int:id>', methods=['PUT', 'DELETE'])
def manage_manual_column(id):
    col = db.session.get(ColumnaManual, id)
    if not col:
        return jsonify({"success": False, "message": "Columna no encontrada"}), 404
        
    if request.method == 'DELETE':
        db.session.delete(col)
        db.session.commit()
        return jsonify({"success": True})
        
    if request.method == 'PUT':
        data = request.json
        if 'nombre' in data: col.nombre = data['nombre'].strip()
        if 'tipo' in data: col.tipo = data['tipo']
        if 'opciones' in data: col.opciones = data.get('opciones', '')
        
        try:
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/config/manual-columns/template')
@login_required
def download_manual_template():
    try:
        cols = ColumnaManual.query.all()
        header = ['ITEMPLAN'] + [c.nombre for c in cols]
        df = pd.DataFrame(columns=header)
        
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Plantilla_Manual')
        except:
            with pd.ExcelWriter(output) as writer:
                df.to_excel(writer, index=False, sheet_name='Plantilla_Manual')
                
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='plantilla_columnas_manuales.xlsx'
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# --- API: CONFIGURACIÓN DE FILTROS ---

@app.route('/api/config/filtros', methods=['GET'])
def get_config_filtros():
    configs = ConfiguracionFiltro.query.all()
    # Si no hay ninguna config, devolvemos un objeto vacío para no romper
    return jsonify({c.columna: {"tipo": c.tipo, "virtual_cols": json.loads(c.virtual_cols_json or '[]')} for c in configs})

@app.route('/api/config/filtros', methods=['POST'])
def update_config_filtro():
    data = request.json
    columna = data.get('columna')
    tipo = data.get('tipo')
    v_cols = data.get('virtual_cols')
    
    config = ConfiguracionFiltro.query.filter_by(columna=columna).first()
    if config:
        if tipo: config.tipo = tipo
        if v_cols is not None: config.virtual_cols_json = json.dumps(v_cols)
    else:
        config = ConfiguracionFiltro(
            columna=columna, 
            tipo=tipo if tipo else 'search',
            virtual_cols_json=json.dumps(v_cols) if v_cols is not None else '[]'
        )
        db.session.add(config)
    db.session.commit()
    return jsonify({"success": True})

# --- API: FILTROS VIRTUALES ---

@app.route('/api/config/filtros-virtuales', methods=['GET'])
def get_filtros_virtuales():
    filtros = FiltroVirtual.query.all()
    return jsonify([f.nombre for f in filtros])

@app.route('/api/config/filtros-virtuales', methods=['POST'])
def add_filtro_virtual():
    nombre = request.json.get('nombre', '').strip().upper()
    if not nombre: return jsonify({"success": False}), 400
    if not FiltroVirtual.query.filter_by(nombre=nombre).first():
        db.session.add(FiltroVirtual(nombre=nombre))
        db.session.commit()
    return jsonify({"success": True})

@app.route('/api/config/filtros-virtuales/<string:nombre>', methods=['DELETE'])
def delete_filtro_virtual(nombre):
    FiltroVirtual.query.filter_by(nombre=nombre).delete()
    db.session.commit()
    return jsonify({"success": True})

# --- API: MAPEOS DE FILTROS ---

@app.route('/api/config/mapeos', methods=['GET'])
def get_mapeos():
    mapeos = MapeoFiltro.query.all()
    return jsonify([{
        "id": m.id,
        "columna_criterio": m.columna_criterio,
        "valor_criterio": m.valor_criterio,
        "valores": json.loads(m.valores_json)
    } for m in mapeos])

@app.route('/api/config/mapeos', methods=['POST'])
def update_mapeo():
    data = request.json
    cc = data.get('columna_criterio')
    vc = data.get('valor_criterio')
    valores = data.get('valores', {})
    
    mapeo = MapeoFiltro.query.filter_by(columna_criterio=cc, valor_criterio=vc).first()
    if mapeo:
        mapeo.valores_json = json.dumps(valores)
    else:
        mapeo = MapeoFiltro(columna_criterio=cc, valor_criterio=vc, valores_json=json.dumps(valores))
        db.session.add(mapeo)
    
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/config/mapeos/<int:id>', methods=['DELETE'])
def delete_mapeo(id):
    MapeoFiltro.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify({"success": True})

# --- API: ACTUALIZACIÓN DE PROYECTO ---

@app.route('/api/proyectos/update-field', methods=['POST'])
@login_required
def update_proyecto_field():
    user_rol = session.get('user_rol')
    if user_rol not in ['Admin', 'Administrador', 'Editor']:
        return jsonify({"success": False, "message": "No autorizado"}), 403

    data = request.json
    id_obra = data.get('id')
    field = data.get('field')
    value = data.get('value')
    
    obra = GestionObra.query.get(id_obra)
    if not obra:
        return jsonify({"success": False, "message": "Proyecto no encontrado"}), 404
        
    data_actual = json.loads(obra.data_json)
    data_actual[field] = value
    obra.data_json = json.dumps(data_actual)
    db.session.commit()
    return jsonify({"success": True})

# --- API: PROYECTOS ---

@app.route('/api/proyectos', methods=['GET'])
@login_required
def get_proyectos():
    user_id = session.get('user_id')
    user_rol = session.get('user_rol')
    user = db.session.get(Usuario, user_id)
    
    # Obtener restricciones del usuario (si no es Admin)
    restricciones = {}
    if user_rol != 'Admin' and user:
        for r in user.restricciones:
            restricciones[r.columna] = json.loads(r.valores_json)

    obras = GestionObra.query.all()
    resultado = []
    hoy = datetime.now()
    
    for o in obras:
        data = json.loads(o.data_json)
        
        # Aplicar filtrado por restricciones
        skip = False
        if restricciones:
            for col, valores_permitidos in restricciones.items():
                val_obra = str(data.get(col, "")).strip()
                if val_obra not in valores_permitidos:
                    skip = True
                    break
        
        if skip:
            continue

        data['__db_id'] = o.id
        
        # Cálculo de Antigüedad (Días)
        antiguedad = ""
        fecha_creacion = data.get('FECHA CREACION IP')
        if fecha_creacion:
            try:
                f_obj = None
                for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
                    try:
                        f_obj = datetime.strptime(str(fecha_creacion).strip(), fmt)
                        break
                    except:
                        continue
                
                if f_obj:
                    diff = hoy - f_obj
                    antiguedad = max(0, diff.days)
            except:
                pass
        
        data['TIMING'] = antiguedad
        resultado.append(data)
    return jsonify(resultado)

@app.route('/api/proyectos/clear', methods=['POST'])
def clear_proyectos():
    GestionObra.query.delete()
    db.session.commit()
    return jsonify({"success": True})

@app.route('/api/proyectos/export', methods=['POST'])
def export_proyectos():
    data = request.json # Data filtrada desde el cliente
    if not data: return jsonify({"error": "No hay datos para exportar"}), 400
    
    df = pd.DataFrame(data)
    if '__db_id' in df.columns: df = df.drop(columns=['__db_id'])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Consolidado')
    
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                     as_attachment=True, download_name=f'Consolidado_ANTON_{datetime.now().strftime("%Y%m%d")}.xlsx')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
