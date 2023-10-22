import tensorflow as tf
print("tpu name: ", tf.test.gpu_device_name())

from tensorflow.python.client import device_lib
print("local devices: ", device_lib.list_local_devices())
