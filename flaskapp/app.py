from flask import Flask, render_template, request
from PIL import Image, ImageEnhance
import numpy as np
import matplotlib.pyplot as plt
import os
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import FileField, SubmitField, FloatField
from wtforms.validators import InputRequired, NumberRange

app = Flask(__name__)
app.config.update(
    SECRET_KEY='secret',
    RECAPTCHA_PUBLIC_KEY='6LefSTIrAAAAADS-eIObBaDZzTweBxygSRsC5Pvg',
    RECAPTCHA_PRIVATE_KEY='6LefSTIrAAAAAOfWkruoykjWN5n4dINe36K8Z6Zx',
    UPLOAD_FOLDER='../static/uploads',
    OUTPUT_FOLDER='../static/outputs'
)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

class BrightnessForm(FlaskForm):
    image = FileField('Изображение', validators=[InputRequired()])
    level = FloatField('Яркость (0.1–3.0)', validators=[InputRequired(), NumberRange(0.1,3.0)])
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

@app.route('/', methods=['GET','POST'])
def index():
    form = BrightnessForm()
    if form.validate_on_submit():
        f = form.image.data; lvl = form.level.data
        in_path = os.path.join(app.config['UPLOAD_FOLDER'], f.filename); f.save(in_path)
        img = Image.open(in_path)
        out = ImageEnhance.Brightness(img).enhance(lvl)
        out_name = f'bright_{lvl}_{f.filename}'; out_path = os.path.join(app.config['OUTPUT_FOLDER'], out_name); out.save(out_path)
        arr_in, arr_out = np.array(img), np.array(out)
        hist_in = os.path.join(app.config['OUTPUT_FOLDER'], 'in_'+f.filename+'.png')
        hist_out = os.path.join(app.config['OUTPUT_FOLDER'], 'out_'+f.filename+'.png')
        plot_histogram(arr_in, hist_in); plot_histogram(arr_out, hist_out)
        return render_template('index.html', form=form, orig=in_path, out=out_path, h1=hist_in, h2=hist_out)
    return render_template('index.html', form=form)

if __name__=='__main__':
    app.run(host='127.0.0.1', port=5000)
