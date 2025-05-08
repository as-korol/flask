import os
import base64
import json
import mimetypes
from io import BytesIO

from flask import Flask, render_template, request, Response, send_from_directory
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SubmitField, FileField, FloatField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileAllowed, FileRequired
from werkzeug.utils import secure_filename
import lxml.etree as ET
from PIL import Image, ImageEnhance
import numpy as np
import matplotlib.pyplot as plt
import shutil

from . import net as neuronet

app = Flask(__name__)
Bootstrap(app)

app.config['SECRET_KEY'] = 'CHANGE_ME_PRIVATE'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LefSTIrAAAAADS-eIObBaDZzTweBxygSRsC5Pvg'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LefSTIrAAAAAOfWkruoykjWN5n4dINe36K8Z6Zx'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(app.root_path, 'static', 'outputs')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

class NetForm(FlaskForm):
    openid = StringField('openid', validators=[DataRequired()])
    upload = FileField('Load image', validators=[file for file in [FileRequired(), FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')]])
    recaptcha = RecaptchaField()
    submit = SubmitField('send')

class BrightnessForm(FlaskForm):
    image = FileField('Изображение', validators=[FileRequired(), FileAllowed(['jpg','png','jpeg'], 'Images only!')])
    level = FloatField('Яркость 0.1–3.0', validators=[DataRequired(), NumberRange(0.1, 3.0)])
    recaptcha = RecaptchaField()
    submit = SubmitField('Применить')

@app.route('/')
def index():
    links = [
        ('Hello world', '/hello'),
        ('Data в шаблоны', '/data_to'),
        ('Классификация (net)', '/net'),
        ('JSON API классификации', '/apinet'),
        ('XML в HTML при помощи XSLT', '/apixml'),
        ('Регулировка яркости, инд. задание. Вариант 3', '/brightness'),
    ]
    return render_template('simple.html', links=links)

@app.route('/hello')
def hello():
    return '<h1>Hello World!</h1>'

@app.route('/data_to')
def data_to():
    return render_template(
        'simple.html',
        some_str='Список людей из some_pars',
        some_value=10,
        some_pars={'user': 'Иван', 'Age': '21'}
    )

@app.route('/net', methods=['GET', 'POST'])
def net():
    form = NetForm()
    filename = None
    results = {}
    if form.validate_on_submit():
        original = secure_filename(form.upload.data.filename)
        ext = os.path.splitext(original)[1] or mimetypes.guess_extension(form.upload.data.mimetype) or ''
        filename = original if os.path.splitext(original)[1] else original + ext
        static_path = os.path.join(app.root_path, 'static', filename)
        form.upload.data.save(static_path)
        shutil.copy(static_path, os.path.join(app.config['OUTPUT_FOLDER'], filename))
        _, images = neuronet.read_image_files(10, os.path.join(app.root_path, 'static'))
        decode = neuronet.getresult(images)
        results = {pred[0][1]: pred[0][2] for pred in decode}
    return render_template('net.html', form=form, image_name=filename, neurodic=results)

@app.route('/brightness', methods=['GET', 'POST'])
def brightness():
    form = BrightnessForm()
    data = {}
    if form.validate_on_submit():
        f = form.image.data
        lvl = form.level.data
        orig = secure_filename(f.filename)
        root, ext = os.path.splitext(orig)
        if not ext:
            ext = mimetypes.guess_extension(f.mimetype) or ''
            orig = root + ext
        in_path = os.path.join(app.config['UPLOAD_FOLDER'], orig)
        f.save(in_path)
        img = Image.open(in_path)
        out_img = ImageEnhance.Brightness(img).enhance(lvl)
        out_name = f'bright_{root}{ext}'
        out_path = os.path.join(app.config['OUTPUT_FOLDER'], out_name)
        out_img.save(out_path)
        def plot(arr, path):
            plt.figure()
            for i, col in enumerate(('r', 'g', 'b')):
                hist, bins = np.histogram(arr[:, :, i].flatten(), bins=256, range=(0, 255))
                plt.plot(bins[:-1], hist, color=col)
            plt.tight_layout()
            plt.savefig(path)
            plt.close()
        plot(np.array(img), os.path.join(app.config['OUTPUT_FOLDER'], f'in_{root}.png'))
        plot(np.array(out_img), os.path.join(app.config['OUTPUT_FOLDER'], f'out_{root}.png'))
        data = {'orig': orig, 'out': out_name, 'hist_in': f'in_{root}.png', 'hist_out': f'out_{root}.png'}
    return render_template('brightness.html', form=form, **data)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/outputs/<path:filename>')
def output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/apinet', methods=['GET', 'POST'])
def apinet():
    if request.method == 'GET':
        return Response(
            json.dumps({'message': 'Use POST with JSON body {"imagebin": "<base64 or data URI>"}'}),
            status=200,
            mimetype='application/json'
        )
    data = {}
    if request.is_json:
        img_data = request.get_json().get('imagebin', '')
        if img_data.startswith('data:'):
            img_data = img_data.split(',', 1)[1]
        try:
            img = Image.open(BytesIO(base64.b64decode(img_data)))
            decode = neuronet.getresult([img])
            data = {pred[0][1]: str(pred[0][2]) for pred in decode}
        except Exception as e:
            return Response(json.dumps({'error': f'Cannot process image: {e}'}), status=400, mimetype='application/json')
    else:
        return Response(json.dumps({'error': 'Content-Type must be application/json'}), status=400, mimetype='application/json')
    return Response(json.dumps(data), status=200, mimetype='application/json')

@app.route('/apixml')
def apixml():
    xml_path = os.path.join(app.root_path, 'static', 'xml', 'file.xml')
    xslt_path = os.path.join(app.root_path, 'static', 'xml', 'file.xslt')
    dom = ET.parse(xml_path)
    xslt = ET.parse(xslt_path)
    newhtml = ET.XSLT(xslt)(dom)
    return Response(str(newhtml), mimetype='text/html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
