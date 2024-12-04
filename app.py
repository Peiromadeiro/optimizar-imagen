from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from PIL import Image, ImageOps
import os
from io import BytesIO
from werkzeug.utils import secure_filename

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
    """Optimiza la imagen cargada."""
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
            
            # Redimensionar manteniendo relación de aspecto y rellenar
            resized_img = resize_with_aspect_ratio(img, 600, 400)

            # Guardar como JPG optimizado
            buffer = BytesIO()
            resized_img.save(buffer, format="JPEG", optimize=True, quality=85)
            buffer.seek(0)

            # Guardar la imagen optimizada localmente (opcional)
            optimized_path = os.path.join(OPTIMIZED_FOLDER, f"optimized_image.jpg")
            with open(optimized_path, 'wb') as f:
                f.write(buffer.read())

            # Devolver la imagen optimizada al cliente
            buffer.seek(0)
            flash("Imagen optimizada con éxito. Descárgala abajo.")
            return send_file(buffer, mimetype='image/jpeg', as_attachment=True, download_name='optimized_image.jpg')
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
