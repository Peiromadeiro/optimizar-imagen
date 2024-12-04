from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from PIL import Image
import os
from io import BytesIO
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret_key_for_flash_messages'

# Configuración de carpetas y formatos permitidos
UPLOAD_FOLDER = 'uploads'
OPTIMIZED_FOLDER = 'optimized'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OPTIMIZED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/optimize', methods=['POST'])
def optimize_image():
    if 'image' not in request.files:
        flash("No se ha seleccionado ninguna imagen.")
        return redirect(url_for('home'))

    file = request.files['image']
    if file.filename == '':
        flash("Por favor, selecciona un archivo válido.")
        return redirect(url_for('home'))

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Guardar la imagen original
            file.save(file_path)

            # Abrir y procesar la imagen
            img = Image.open(file_path)
            img = img.resize((600, 400), Image.ANTIALIAS)

            # Convertir a formato JPEG para optimización
            buffer = BytesIO()
            img_format = 'JPEG' if img.format != 'PNG' else 'PNG'
            img.save(buffer, format=img_format, optimize=True, quality=85)
            buffer.seek(0)

            # Guardar la imagen optimizada
            optimized_path = os.path.join(OPTIMIZED_FOLDER, f"optimized_{filename}")
            with open(optimized_path, 'wb') as f:
                f.write(buffer.read())

            flash("Imagen optimizada con éxito. Descárgala abajo.")
            return send_file(buffer, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=f'optimized_{filename}')
        except Exception as e:
            flash(f"Error al procesar la imagen: {e}")
            return redirect(url_for('home'))
    else:
        flash("Formato no admitido. Usa PNG, JPG, JPEG, WEBP, BMP o TIFF.")
        return redirect(url_for('home'))

if __name__ == '__main__':
    import os

port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
