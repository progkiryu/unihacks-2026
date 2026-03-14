from flask import Blueprint, request, jsonify
from .services import say_hello
import os
from werkzeug.utils import secure_filename

api = Blueprint("api", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@api.route("/hello", methods=["GET"])
def hello():
    message = say_hello()
    return {"message": message}

@api.route("/photo", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        return jsonify({"message": f"File {filename} uploaded successfully!"}), 200

    return jsonify({"error": "File type not allowed"}), 400
