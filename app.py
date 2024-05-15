"""
Une application Flask pour voir les photos des oiseaux capturés!
"""
import base64

from PIL import Image
import io
from flask import Flask, render_template, jsonify, request, redirect, url_for
import os
import bd
import requests
from datetime import datetime
import hashlib

app = Flask(__name__)

app.secret_key = 'your_secret_key'

def encrypt_string(hash_string):
    sha_signature = hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

@app.route("/")
def index():
    lstImages = []
    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute("SELECT * FROM images")
            for row in curseur.fetchall():
                lstImages.append(row)

    return render_template("index.html", lstImages=lstImages)


@app.route("/api/upload-image", methods=["POST"])
def upload_image():
    token = request.form.get("token")
    if token is None:
        return jsonify({"error": "Unauthorized"}), 401

    if encrypt_string(app.secret_key) != token:
        return jsonify({"error": "Unauthorized"}), 401

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    image = Image.open(file)

    byte_arr = io.BytesIO()
    image.save(byte_arr, format='JPEG')  # Change 'JPEG' to your image's format

    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            current_date = datetime.now().strftime('%Y-%m-%d')
            curseur.execute("INSERT INTO images (date) VALUES (%s)", (current_date,))
            image_id = curseur.lastrowid

    image_path = os.path.join("static/images/", str(image_id) + ".jpg")
    image.save(image_path)

    return jsonify({"success": True, "image_id": image_id}), 200

@app.route("/details/<int:image_id>", methods=["GET"])
def get_image(image_id):
    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute("SELECT * FROM images WHERE id = %s", (image_id,))
            image = curseur.fetchone()
            if not image:
                return "Image not found", 404

    return render_template("details.html", image=image)

@app.route("/api/delete-image/<int:image_id>")
def delete_image(image_id):
    with bd.creer_connexion() as conn:
        with conn.get_curseur() as curseur:
            curseur.execute("DELETE FROM images WHERE id = %s", (image_id,))

    os.remove(os.path.join("static/images", str(image_id)+".jpg"))

    return redirect(url_for("index"))

@app.route("/api/token", methods=["POST"])
def get_token():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == "admin" and password == "password":
        return jsonify({"token": encrypt_string(app.secret_key)}), 200


## TODO : CETTE FONCTION EST A UTILISER DANS LE PROGRAMME DE CAPTURE D'IMAGES
def envoyer_image():
    url = "http://localhost:5000/api/upload-image"  # Remplacez par l'URL de votre API
    filename = "static/images/Oiseau.jpg"  # Remplacez par le chemin vers votre image

    with open(filename, 'rb') as f:
        image_data = f.read()

    file = {'file': image_data}

    response = requests.post(url, files=file, data={"token": "CHANGE_BY_THE_TOKEN_GENERATED_BY_THE_SERVER"})

    if response.status_code == 200:
        print("Image envoyée avec succès.")

    else:
        print("Erreur lors de l'envoi de l'image.")

    return response.json()



