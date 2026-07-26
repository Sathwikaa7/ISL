import tensorflow as tf
import matplotlib.pyplot as plt

dataset_path = r"D:\SLD\dataset"

test_ds = tf.keras.utils.image_dataset_from_directory(
    dataset_path,
    validation_split=0.2,
    subset="validation",
    seed=42,
    image_size=(224,224),
    batch_size=32
)

normalization_layer = tf.keras.layers.Rescaling(1./255)

test_ds = test_ds.map(lambda x,y:(normalization_layer(x),y))

model = tf.keras.models.load_model("model/isl_model.keras")

loss, accuracy = model.evaluate(test_ds)

print("Accuracy:",accuracy)