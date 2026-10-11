from flask import Flask, request, render_template, redirect, url_for, flash
from tensorflow.keras.models import load_model
import numpy as np
from PIL import Image
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

MODEL_PATH = os.path.join(BASE_DIR, 'model.h5')
model = load_model(MODEL_PATH)

def preprocess_image(image):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image = image.resize((100, 100))
    img = np.array(image, dtype=np.float32) / 255.0
    return img.reshape(1, 100, 100, 3)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return redirect(url_for('index'))

    file = request.files['image']

    if file.filename == '':
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    if not filename:
        filename = f"{uuid.uuid4().hex}.jpg"

    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    image = Image.open(save_path)
    x = preprocess_image(image)

    proba = float(model.predict(x)[0][0])

    if proba <= 0.3:
        result = "Cat"
    elif proba >= 0.7:
        result = "Dog"
    else:
        result = "Uncertain"

    return render_template(
        'index.html',
        result=result,
        probability=round(proba, 4),
        image_path=url_for('static', filename=f'uploads/{filename}')
    )

if __name__ == '__main__':
    app.run(debug=True)
