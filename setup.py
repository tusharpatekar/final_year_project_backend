from flask import Flask, render_template, redirect, request, url_for, send_from_directory, flash,jsonify
from flask_cors import CORS
from google.oauth2 import id_token
from google.auth.transport import requests
import store
from werkzeug.utils import secure_filename
import os
import tensorflow
import numpy as np
import pickle
import sqlite3
import support

app = Flask(__name__)
CORS(app)
app.secret_key = 'b\xa3\xdf\x96\xd2...'
def setup_database():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Call the setup function

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'model')

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'bucket')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'JPG'}

MODEL = tensorflow.keras.models.load_model(os.path.join(MODEL_DIR, 'vgg.h5'))
REC_MODEL = pickle.load(open(os.path.join(MODEL_DIR, 'RF.pkl'), 'rb'))

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



CLASSES = ['Apple scab', 'Apple Black rot', 'Apple Cedar apple rust', 'Apple healthy', 'Blueberry healthy', 'Cherry (including sour) Powdery mildew', 'Cherry (including sour) healthy', 'Corn (maize) Cercospora leaf spot Gray leaf spot', 'Corn(maize) Common rust', 'Corn(maize) Northern Leaf Blight', 'Corn(maize) healthy', 'Grape Black rot', 'Grape Esca(Black Measles)', 'Grape Leaf blight(Isariopsis Leaf Spot)', 'Grape healthy', 'Orange Haunglongbing(Citrus greening)', 'Peach Bacterial spot', 'Peach healthy', 'Bell PepperBacterial_spot', 'Pepper bell healthy', 'Potato Early blight', 'Potato Late blight', 'Potato healthy', 'Raspberry healthy', 'Soybean healthy', 'Squash Powdery mildew', 'Strawberry Leaf scorch', 'Strawberry healthy', 'Tomato Bacterial spot', 'Tomato Early blight', 'Tomato Late blight', 'Tomato Leaf Mold', 'Tomato Septoria leaf spot', 'Tomato Spider mites (Two-spotted spider mite)', 'Tomato Target Spot', 'Tomato Yellow Leaf Curl Virus', 'Tomato mosaic virus', 'Tomato healthy']
def connect_db():
    return sqlite3.connect('store.db')




@app.route('/google-login', methods=['POST'])
def google_login():
    data = request.get_json()
    token = data.get('token')

    try:
        # Replace YOUR_GOOGLE_CLIENT_ID with your actual client ID
        CLIENT_ID = "763127770724-isjj3oae0bug2vk42ueo8090h4je9jpa.apps.googleusercontent.com"

        # Verify the token
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)

        # Extract user information from the token
        email = idinfo.get('email')
        name = idinfo.get('name')

        # Check if the user exists in the database
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()

        if not user:
            # If the user doesn't exist, create a new user
            cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, ''))
            conn.commit()

        conn.close()

        return jsonify({"message": "Google Login successful", "email": email, "status":"true"}), 200
    except ValueError as e:
        # Invalid token
        return jsonify({"error": "Invalid token", "status":"false"}), 400
    

# Signup API
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
        conn.commit()
        conn.close()
        return jsonify({"message": "Signup successful"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400

# Login API
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"error": "Invalid email or password"}), 401




@app.route('/')
def home():
        return render_template("index.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @app.route('/about')
def aboutme():
    return render_template('about.html')

@app.route('/plantdisease/<res>')
def plantresult(res):
    print(res)
    corrected_result = ""
    for i in res:
        if i!='_':
            corrected_result = corrected_result+i
    return render_template('plantdiseaseresult.html', corrected_result=corrected_result)


@app.route('/plantdisease', methods=['POST'])
def plantdisease():
    if 'file' not in request.files:
        return {"error": "No file part"}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {"error": "No selected file"}, 400

    # Validate file type
    if not allowed_file(file.filename):
        return {"error": "Invalid file type"}, 400
    # If validation passes, save the file and process it
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)


    imagefile = tensorflow.keras.utils.load_img(
        os.path.join(app.config['UPLOAD_FOLDER'], filename),
        target_size=(224, 224, 3)
    )
    input_arr = tensorflow.keras.preprocessing.image.img_to_array(imagefile)
    input_arr = np.array([input_arr])

    predict = MODEL.predict(input_arr)
    probability_model = tensorflow.keras.Sequential([MODEL, tensorflow.keras.layers.Softmax()])
    predict_probs = probability_model.predict(input_arr)
    p = np.argmax(predict_probs[0])
    dis = p
    res = support.get_more_info(filepath, dis)
    
    return {"result": res}



#@app.route('/croprecommendation/<res>')
def cropresult(res):
    print(res)
    corrected_result = res
    return render_template('croprecresult.html', corrected_result=corrected_result)

#@app.route('/croprecommendation', methods=['GET', 'POST'])
def cr():
    if request.method == 'POST':
        X = []
        if request.form.get('nitrogen'):
            X.append(float(request.form.get('nitrogen')))
        if request.form.get('phosphorous'):
            X.append(float(request.form.get('phosphorous')))
        if request.form.get('potassium'):
            X.append(float(request.form.get('potassium')))
        if request.form.get('temperature'):
            X.append(float(request.form.get('temperature')))
        if request.form.get('humidity'):
            X.append(float(request.form.get('humidity')))
        if request.form.get('ph'):
            X.append(float(request.form.get('ph')))
        if request.form.get('rainfall'):
            X.append(float(request.form.get('rainfall')))
        X = np.array(X)
        X = X.reshape(1, -1)
        res = REC_MODEL.predict(X)[0]
        # print(res)
        return redirect(url_for('cropresult', res=res))
    return render_template('croprec.html')




if __name__== "__main__":
    setup_database()
    app.run(debug=True)