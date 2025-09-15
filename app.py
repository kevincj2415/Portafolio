from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import uuid
from pathlib import Path
from bson.objectid import ObjectId
from flask import Response, abort
import gridfs

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración de subida
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# Limitar tamaño máximo de petición (ej. 3 * 1024 * 1024 = 3MB)
app.config['MAX_CONTENT_LENGTH'] = 3 * 1024 * 1024

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'image')
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Conexión a MongoDB usando la configuración
mongo_uri = os.getenv('MONGODB_URI')
cliente = MongoClient(mongo_uri)

# Seleccionar base de datos
app.db = cliente.Portafolio
# Instancia de GridFS para la base de datos Portafolio
fs = gridfs.GridFS(app.db)


@app.route('/')
def index():
    proyectos = [proyecto for proyecto in app.db.proyectos.find({})]
    habilidades = [habilidad for habilidad in app.db.habilidades.find({})]
    return render_template('index.html', proyectos=proyectos, habilidades=habilidades)

@app.route('/ingresar')
def ingresar():
    return render_template('ingresar.html')

@app.route('/central')
def central():
    proyectos = [proyecto for proyecto in app.db.proyectos.find({})]
    habilidades = [habilidad for habilidad in app.db.habilidades.find({})]
    return render_template('central.html', proyectos=proyectos, habilidades=habilidades)

@app.route('/passar', methods=['POST'])
def passar():
    username = request.form.get('username')
    password = request.form.get('password')

    # Verificar si el usuario existe
    usuario = app.db.usuarios.find_one({'nombre': username})
    if usuario is None:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    if usuario['contraseña'] != password:
        return jsonify({'error': 'Contraseña incorrecta'}), 401
    else:
        return redirect('/central')
    
@app.route('/agregar_proyecto', methods=['POST'])
def agregar_proyecto():
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    github = request.form.get('github')
    url = request.form.get('url')
    # Manejo seguro de imagen
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    # Usar GridFS para almacenar la imagen y guardar la referencia (ObjectId)
    imagen_id = None
    if 'imagen' in request.files:
        imagen = request.files.get('imagen')
        if imagen and imagen.filename:
            filename = imagen.filename
            if not allowed_file(filename):
                return jsonify({'error': 'Formato de imagen no permitido'}), 400
            safe_name = secure_filename(filename)
            try:
                # Guardar en GridFS. flask `FileStorage` es un stream file-like
                imagen_id = fs.put(imagen.stream, filename=safe_name, content_type=imagen.content_type)
            except Exception as e:
                return jsonify({'error': f'Error al guardar la imagen en GridFS: {str(e)}'}), 500
    # Guardar en MongoDB
    app.db.proyectos.insert_one({
        'nombre': nombre,
        'descripcion': descripcion,
        'github': github,
        'url': url,
        'imagen_id': imagen_id
    })
    return redirect('/central')  # Ajusta según tu ruta


@app.route('/imagen/<id>')
def imagen(id):
    try:
        archivo = fs.get(ObjectId(id))
        return Response(archivo.read(), mimetype=archivo.content_type)
    except Exception:
        abort(404)

@app.route('/agregar_habilidad', methods=['POST'])
def agregar_habilidad():
    tecnologia = request.form['tecnologia']
    experiencia = request.form['experiencia']
    imagen_url = request.form['imagen']
    proyectos = request.form.get('proyectos', '').splitlines()
    descripcion = request.form.get('descripcion')
    app.db.habilidades.insert_one({'tecnologia': tecnologia,
                                   'experiencia': experiencia,
                                   'imagen': imagen_url,
                                   'proyectos': proyectos,
                                   'descripcion': descripcion})
    return redirect('/central')

if __name__ == '__main__':
    app.run(debug = True, port=1225)
