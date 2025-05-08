from flask import Flask, render_template, request, send_from_directory
from PIL import Image, ImageEnhance
import numpy as np
import matplotlib.pyplot as plt
import os
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import FileField, SubmitField, FloatField
from wtforms.validators import InputRequired, NumberRange

app = Flask(__name__)
app.config.update(
    SECRET_KEY='CHANGE_ME',
    RECAPTCHA_PUBLIC_KEY='6LefSTIrAAAAADS-eIObBaDZzTweBxygSRsC5Pvg',
    RECAPTCHA_PRIVATE_KEY='6LefSTIrAAAAAOfWkruoykjWN5n4dINe36K8Z6Zx',
    UPLOAD_FOLDER='../static/uploads',
    OUTPUT_FOLDER='../static/outputs'
)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

class BrightnessForm(FlaskForm):
    image = FileField('Изображение', validators=[InputRequired()])
    level = FloatField('Яркость 0.1–3.0', validators=[InputRequired(), NumberRange(0.1,3.0)])
    recaptcha = RecaptchaField()
    submit = SubmitField('Применить')

def plot_histogram(arr, path):
    plt.figure()
    for i,col in enumerate(('r','g','b')):
        hist,bins = np.histogram(arr[:,:,i].flatten(), bins=256, range=(0,255))
        plt.plot(bins[:-1], hist, color=col)
    plt.xlabel('Интенсивность')
    plt.ylabel('Частота')
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/outputs/<path:filename>')
def output_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/', methods=['GET','POST'])
def index():
    form = BrightnessForm()
    if form.validate_on_submit():
        f = form.image.data
        lvl = form.level.data

        orig_name = f.filename
        in_path = os.path.join(app.config['UPLOAD_FOLDER'], orig_name)
        f.save(in_path)

        img = Image.open(in_path)
        out = ImageEnhance.Brightness(img).enhance(lvl)
        base, ext = os.path.splitext(orig_name)

        out_name = f'bright_{lvl}_{base}{ext}'
        out_path = os.path.join(app.config['OUTPUT_FOLDER'], out_name)
        out.save(out_path)

        hist_in_name  = f'in_{base}.png'
        hist_out_name = f'out_{base}.png'
        hist_in_path  = os.path.join(app.config['OUTPUT_FOLDER'], hist_in_name)
        hist_out_path = os.path.join(app.config['OUTPUT_FOLDER'], hist_out_name)

        plot_histogram(np.array(img), hist_in_path)
        plot_histogram(np.array(out), hist_out_path)

        return render_template('index.html',
                               form=form,
                               orig_filename=orig_name,
                               out_filename=out_name,
                               hist_in_filename=hist_in_name,
                               hist_out_filename=hist_out_name)
    return render_template('index.html', form=form)

if __name__=='__main__':
    app.run(host='127.0.0.1', port=5000)
