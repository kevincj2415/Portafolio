from flask import Flask, request, jsonify, render_template, redirect, url_for
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Conexión a MongoDB usando la configuración
mongo_uri = os.getenv('MONGODB_URI')
cliente = MongoClient(mongo_uri)

# Seleccionar base de datos
app.db = cliente.Portafolio


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
    imagen = request.files['imagen']
    # Guardar imagen en static/image
    if imagen:
        ruta = os.path.join('static', 'image', imagen.filename)
        imagen.save(ruta)
        imagen_url = f'/static/image/{imagen.filename}'
    else:
        imagen_url = None
    # Guardar en MongoDB
    app.db.proyectos.insert_one({
        'nombre': nombre,
        'descripcion': descripcion,
        'github': github,
        'url': url,
        'imagen_url': imagen_url
    })
    return redirect('/central')  # Ajusta según tu ruta

@app.route('/agregar_habilidad', methods=['POST'])
def agregar_habilidad():
    tecnologia = request.form['tecnologia']
    experiencia = request.form['experiencia']
    imagen = request.form['imagen']
    proyectos = request.form['proyectos'].splitlines()
    descripcion = request.form['descripcion']
    app.db.habilidades.insert_one({'tecnologia': tecnologia,
                                   'experiencia': experiencia,
                                   'imagen': imagen,
                                   'proyectos': proyectos,
                                   'descripcion': descripcion})
    return redirect('/central')

if __name__ == '__main__':
    app.run(debug = True, port=1224)
