from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from config import Config
from services.inference import InferenceEngine


app = Flask(__name__)
app.config.from_object(Config)
engine = InferenceEngine(
    model_path=app.config["MODEL_PATH"],
    labels_path=app.config["LABELS_PATH"],
    img_size=app.config["IMG_SIZE"],
    sensor_config_path=app.config["SENSOR_CONFIG_PATH"],
)


@app.get("/")
def index():
    return render_template("index.html")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


def parse_sensor_values(payload: dict) -> tuple[float, float, float]:
    try:
        mq135 = float(payload.get("mq135", 0))
        mq2 = float(payload.get("mq2", 0))
        mq3 = float(payload.get("mq3", 0))
    except (TypeError, ValueError):
        raise ValueError("Input sensor harus berupa angka valid.")

    if mq135 < 0 or mq2 < 0 or mq3 < 0:
        raise ValueError("Nilai sensor tidak boleh negatif.")

    return mq135, mq2, mq3


@app.post("/sensor/calculate")
def sensor_calculate():
    payload = request.get_json(silent=True) or {}
    try:
        mq135, mq2, mq3 = parse_sensor_values(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    analysis = engine.calculate_sensor_metrics({"mq135": mq135, "mq2": mq2, "mq3": mq3})
    return jsonify(analysis)


@app.post("/predict")
def predict():
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)

    image_file = request.files.get("image")
    if image_file is None or image_file.filename == "":
        return jsonify({"error": "File gambar wajib diunggah."}), 400

    if not allowed_file(image_file.filename):
        return jsonify({"error": "Format file harus JPG, JPEG, atau PNG."}), 400

    filename = secure_filename(image_file.filename)
    upload_path = app.config["UPLOAD_FOLDER"] / filename
    image_file.save(upload_path)

    try:
        mq135, mq2, mq3 = parse_sensor_values(request.form)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        result = engine.predict(upload_path, {"mq135": mq135, "mq2": mq2, "mq3": mq3})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(result)


if __name__ == "__main__":
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
    app.run(debug=True)
