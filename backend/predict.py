import numpy as np
import tensorflow as tf
from PIL import Image

# Load model only once
model = tf.keras.models.load_model("models/isl_word_model.keras")

# Class names (must match the training order)
CLASS_NAMES = [
    'afternoon','animal','bad','beautiful','big','bird','blind','cat',
    'cheap','clothing','cold','cow','curved','deaf','dog','dress',
    'dry','evening','expensive','famous','fast','female','fish','flat',
    'friday','good','happy','hat','healthy','horse','hot','hour',
    'light','long','loose','loud','minute','monday','month','morning',
    'mouse','narrow','new','night','old','pant','pocket','quiet',
    'sad','saturday','second','shirt','shoes','short','sick','skirt',
    'slow','small','suit','sunday','t_shirt','tall','thursday','time',
    'today','tomorrow','tuesday','ugly','warm','wednesday','week',
    'wet','wide','year','yesterday','young'
]

def predict_image(image_path):

    image = Image.open(image_path).convert("RGB")

    image = image.resize((224,224))

    image = np.array(image, dtype=np.float32)

    image = tf.keras.applications.mobilenet_v3.preprocess_input(image)

    image = np.expand_dims(image, axis=0)

    prediction = model.predict(image, verbose=0)

    index = np.argmax(prediction)

    confidence = float(prediction[0][index])

    return CLASS_NAMES[index], confidence