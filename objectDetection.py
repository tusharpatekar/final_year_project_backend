from tensorflow import keras
from tensorflow.keras import layers

# Load the VGG16 model
base_model = keras.applications.VGG16(
    weights='imagenet',   # Pre-trained weights on ImageNet
    input_shape=(224, 224, 3),
    include_top=False     # Exclude fully connected layers at the top
)

# Freeze the base model layers
base_model.trainable = False

# Define the input layer
inputs = keras.Input(shape=(224, 224, 3))

# Pass inputs through the base model
x = base_model(inputs, training=False)

# Add custom layers for object detection
x = layers.GlobalAveragePooling2D()(x)  # Pooling layer
x = layers.Dropout(0.2)(x)              # Dropout for regularization
outputs = layers.Dense(38, activation='softmax')(x)  # Output layer for 38 classes

# Create the model
vgg16_model = keras.Model(inputs, outputs, name='pretrained_vgg16')

# Compile the model
vgg16_model.compile(optimizer=keras.optimizers.Adam(),
                    loss=keras.losses.CategoricalCrossentropy(from_logits=False),
                    metrics=[keras.metrics.CategoricalAccuracy()])

# Display the model summary
vgg16_model.summary()