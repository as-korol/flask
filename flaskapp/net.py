import os
from PIL import Image
import numpy as np
from keras.layers import Input
from keras.applications.resnet_v2 import ResNet50V2, decode_predictions

visible = Input(shape=(224, 224, 3), name='imginp')
resnet = ResNet50V2(include_top=True, weights='imagenet', input_tensor=visible)

def read_image_files(files_max_count, dir_name):
    files = [f.name for f in os.scandir(dir_name) if f.is_file()]
    count = min(files_max_count, len(files))
    images = []
    for i in range(count):
        images.append(Image.open(os.path.join(dir_name, files[i])))
    return count, images

def getresult(image_list):
    arr = np.array([np.array(img.resize((224, 224))) / 255.0 for img in image_list])
    out = resnet.predict(arr)
    return decode_predictions(out, top=1)