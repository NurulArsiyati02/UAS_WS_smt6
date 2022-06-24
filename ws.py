# ====== NAMA KELOMPOK =====
#  MOH IZZUL FUADI ====== KELAS 6D ====== 19090032
#  NURUL ARSIYATI  ====== KELAS 6B ====== 19090045

import json
import pymongo
from bson.objectid import ObjectId
import os
import random
import string
import sys
import numpy as np
from util import base64_to_pil
from flask import Flask, redirect, url_for, request, render_template, Response, jsonify, session
from werkzeug.utils import secure_filename
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.applications.imagenet_utils import preprocess_input, decode_predictions
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.utils import get_file


app = Flask(__name__)

app.secret_key = 'MySecret'

# ========== SETUP MONGODB ==========
try:
    mongo = pymongo.MongoClient(
        host="localhost",
        port=27017,
        serverSelectionTimeoutMS=1000
    )
    db = mongo.bigproject
    mongo.server_info()
except:
    print("ERROR Connect To Database")

# ===================================


# ========== PREDICT ==========
model = load_model('models/model_food.h5')


def model_predict(img, model):
    img = img.resize((224, 224))
    x = image.img_to_array(img)
    x = x.reshape(-1, 224, 224, 3)
    x = x.astype('float32')
    x = x / 255.0
    preds = model.predict(x)
    return preds


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Request gambar
        img = base64_to_pil(request.json)
        print(request.json)
        # Simpan Gambar
        img.save("uploads/plant.png")
        # Membuat Prediksi
        preds = model_predict(img, model)

        target_names = [
            'Bread', 'Dairy_product', 'Dessert', 'Egg', 'Fried_food'
        ]

        hasil_label = target_names[np.argmax(preds)]
        data = list(db.food.find())

        for i, bread in enumerate(target_names):
            if hasil_label == bread:
                jenis_makanan = data[i]["jenis"]
                deskripsi_makanan = data[i]["deskripsi"]
                kandungan_makanan = data[i]["nutrisi"]
                manfaat_makanan = data[i]["manfaat"]

        # 2f adalah presisi angka dibelakang koma (coba ganti jadi 0f, 3f, dst)
        hasil_prob = "{:.2f}".format(100 * np.max(preds))

        return jsonify(
            result=hasil_label,
            probability=hasil_prob + str('%'),
            jenis=jenis_makanan,
            deskripsi=deskripsi_makanan,
            nutrisi=kandungan_makanan,
            manfaat=manfaat_makanan
        )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Cannot Predict!"}),
            status=500,
            mimetype="application/json"
        )
# =======================================


# ========== CREATE USER ==========
@app.route("/users/create", methods=["POST"])
def create_user():
    try:
        user = {
            "username": request.json["username"],
            "password": request.json["password"],
            "token": request.json["token"]
        }
        dbResponse = db.login.insert_one(user)
        session['username'] = request.json["username"]
        return Response(
            response=json.dumps({
                "message": "User Created",
                "id": f"{dbResponse.inserted_id}"
            }),
            status=200,
            mimetype="application/json"
        )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Cannot Create User!"}),
            status=500,
            mimetype="application/json"
        )

# ==================================


# ========== LOGIN USER ==========
@app.route("/users/login", methods=["POST"])
def login_user():
    try:
        login_user = db.login.find_one({'username': request.form["username"]})
        if login_user:
            if request.form["password"] == login_user["password"]:
                db.login.update_one(
                    {"_id": login_user["_id"]},
                    {"$set": {
                        "token": ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                    }}
                )
                session["username"] = login_user["username"]
                return redirect('/admin')
                # return Response(
            #         response=json.dumps({
            #             "message": "Token Updated!"
            #         }),
            #         status=200,
            #         mimetype="application/json"
            #     )
            else:
                return Response(
                    response=json.dumps(
                        {"Message": "Password Yang Anda Masukan Salah!"}),
                    status=500,
                    mimetype="application/json"
                )
                # return redirect('/login')
        else:
            return Response(
                response=json.dumps(
                    {"Message": "Username Yang Anda Masukan Salah!"}),
                status=500,
                mimetype="application/json"
            )
            # return redirect('/login')
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Login Gagal!"}),
            status=500,
            mimetype="application/json"
        )

# ======================================


# ========================================
@ app.route("/admin")
def pindai():
    return render_template('admin.html')


@ app.route("/addplant")
def addplant():
    return render_template('addplant.html')


@ app.route("/login")
def login():
    return render_template('login.html')


@ app.route("/logout")
def logout():
    session["username"] = None
    return redirect("/login")


# ========================================


# ========== CREATE PLANT ==========
@ app.route("/plants/create", methods=["POST"])
def create_plant():
    try:
        # if not session.get("username"):
            # if not there in the session then redirect to the login page
            # return redirect("/login")
        # token = db.users.find_one({"token": request.form["token"]})
        # if token:
        plant = {
            "nama": request.form["nama"],
            "jenis": request.form["jenis"],
            "deskripsi": request.form["deskripsi"],
            "nutrisi": request.form["nutrisi"],
            "manfaat": request.form["manfaat"]
        }
        dbResponse = db.food.insert_one(plant)
        return redirect('/plants')
        # return Response(
        #      response=json.dumps({
        #          "message": "Plant Created",
        #          "id": f"{dbResponse.inserted_id}"
        #      }),
        #      status=200,
        #      mimetype="application/json"
        # )
        #else:
            # return Response(
            #     response=json.dumps({
            #         "message": "Token Salah!"
            #     }),
            #     status=500,
            #     mimetype="application/json"
            # )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Cannot Create Plant!"}),
            status=500,
            mimetype="application/json"
        )

# =======================================


# ========== READ ==========
@ app.route("/plants", methods=["GET"])
def get_plants():
    try:
        # if not session.get("username"):
            # if not there in the session then redirect to the login page
            # return redirect("/login")
        # token = db.users.find_one({"token": request.json["token"]})
        # if token:
        data = list(db.food.find())
        # Convert to string
        for plant in data:
            plant["_id"] = str(plant["_id"])
        return render_template('listplant.html', dataplant=enumerate(data))
        # return Response(
        #     response=json.dumps(data),
        #     status=200,
        #     mimetype="application/json"
        # )
    #     else:
    #         return Response(
    #             response=json.dumps({
    #                 "message": "Token Salah!"
    #             }),
    #             status=500,
    #             mimetype="application/json"
    #         )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({
                "message": "Cannot Get Plants!"
            }),
            status=500,
            mimetype="application/json"
        )

# ============================================


# ========== UPDATE ==========
@ app.route("/plants/update/<id>", methods=["PUT"])
def update_plant(id):
    try:
        token = db.users.find_one({"token": request.json["token"]})
        if token:
            dbResponse = db.plants.update_one(
                {"_id": ObjectId(id)},
                {"$set": {
                    "nama": request.json["nama"],
                    "jenis": request.json["jenis"],
                    "deskripsi": request.json["deskripsi"],
                    "nutrisi": request.json["nutrisi"],
                    "manfaat": request.json["manfaat"]
                }}
            )
            if dbResponse.modified_count == 1:
                return Response(
                    response=json.dumps({"message": "Plant Updated"}),
                    status=200,
                    mimetype="application/json"
                )
            else:
                return Response(
                    response=json.dumps({"message": "Nothing To Update"}),
                    status=200,
                    mimetype="application/json"
                )
        else:
            return Response(
                response=json.dumps({
                    "message": "Token Salah!"
                }),
                status=500,
                mimetype="application/json"
            )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Sorry Cannot Update!"}),
            status=500,
            mimetype="application/json"
        )

# ====================================================


# ========== DELETE ==========
@ app.route("/plants/delete/<id>", methods=["DELETE"])
def delete_plant(id):
    try:
        token = db.users.find_one({"token": request.json["token"]})
        if token:
            dbResponse = db.plants.delete_one({"_id": ObjectId(id)})
            if dbResponse.deleted_count == 1:
                return Response(
                    response=json.dumps({
                        "message": "Plant Deleted",
                        "id": f"{id}"
                    }),
                    status=200,
                    mimetype="application/json"
                )
            else:
                return Response(
                    response=json.dumps({
                        "message": "Plant Not Found",
                        "id": f"{id}"
                    }),
                    status=200,
                    mimetype="application/json"
                )
        else:
            return Response(
                response=json.dumps({
                    "message": "Token Salah!"
                }),
                status=500,
                mimetype="application/json"
            )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Sorry Cannot Delete!"}),
            status=500,
            mimetype="application/json"
        )

# ===============================================


if __name__ == "__main__":
    app.run(port=8000, debug=True)