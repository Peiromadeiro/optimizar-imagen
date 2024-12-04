from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from PIL import Image, ImageOps
import os
from io import BytesIO
from werkzeug.utils import secure_filename
import requests

# Configuración de la aplicación
app = Flask(__name__)
app.secret_key = 'secret_key_for_flash_messages'

# Carpetas y formatos permitidos
UPLOAD_FOLDER = 'uploads'
OPTIMIZED_FOLDER = 'optimized'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OPTIMIZED_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_with_aspect_ratio(image, target_width, target_height, background_color=(255, 255, 255)):
    """Redimensiona la imagen manteniendo la relación de aspecto, rellenando con color de fondo."""
    img = ImageOps.contain(image, (target_width, target_height), method=Image.Resampling.LANCZOS)
    background = Image.new('RGB', (target_width, target_height), background_color)
    offset = ((target_width - img.width) // 2, (target_height - img.height) // 2)
    background.paste(img, offset)
    return background

@app.route('/')
def home():
    """Renderiza la página principal."""
    return render_template('index.html')

@app.route('/optimize', methods=['POST'])
def optimize_image():
    """Optimiza la imagen cargada o descargada desde una URL."""
    image = None

    # Comprobar si se subió un archivo
    if 'image' in request.files and request.files['image'].filename != '':
        file = request.files['image']
        if allowed_file(file.filename):
            image = Image.open(file)
        else:
            flash("Formato no admitido. Usa PNG, JPG, JPEG, WEBP, BMP o TIFF.")
            return redirect(url_for('home'))

    # Comprobar si se proporcionó una URL
    elif 'image_url' in request.form and request.form['image_url']:
        url = request.form['image_url']
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
        except Exception as e:
            flash(f"No se pudo descargar la imagen de la URL: {e}")
            return redirect(url_for('home'))

    # Si no se proporcionó ni archivo ni URL
    if image is None:
        flash("Por favor, selecciona una imagen o proporciona una URL válida.")
        return redirect(url_for('home'))

    # Procesar la imagen
    try:
        resized_img = resize_with_aspect_ratio(image, 600, 400)

        # Guardar como JPG optimizado
        buffer = BytesIO()
        resized_img.save(buffer, format="JPEG", optimize=True, quality=85)
        buffer.seek(0)

        # Configurar la respuesta para forzar la descarga
        return send_file(
            buffer,
            mimetype='image/jpeg',
            as_attachment=True,  # Esto fuerza la descarga
            download_name='optimized_image.jpg'  # Nombre del archivo descargado
        )
    except Exception as e:
        flash(f"Error al procesar la imagen: {e}")
        return redirect(url_for('home'))

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

