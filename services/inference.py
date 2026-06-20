from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
from PIL import Image

try:
    import tensorflow as tf
except Exception:  # pragma: no cover
    tf = None


@dataclass
class PredictionResult:
    grade_label: str
    model_confidence: float
    aroma_score: float
    sensor_analysis: Dict[str, object]
    probabilities: Dict[str, float]
    model_ready: bool


class InferenceEngine:
    def __init__(self, model_path: Path, labels_path: Path, img_size: int = 224, sensor_config_path: Path = None):
        self.model_path = Path(model_path)
        self.labels_path = Path(labels_path)
        self.sensor_config_path = Path(sensor_config_path) if sensor_config_path else None
        self.img_size = img_size
        self._model = None
        self._labels = self._load_labels()
        self._sensor_config = self._load_sensor_config()

    def _load_sensor_config(self) -> Dict[str, object]:
        if not self.sensor_config_path or not self.sensor_config_path.exists():
            raise FileNotFoundError("File konfigurasi sensor_config.json tidak ditemukan atau path tidak diatur.")
        with self.sensor_config_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _load_labels(self) -> List[str]:
        if self.labels_path.exists():
            if self.labels_path.suffix.lower() == ".json":
                with self.labels_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return [str(item) for item in data]
                if isinstance(data, dict):
                    return [str(v) for _, v in sorted(data.items(), key=lambda x: int(x[0]))]
            with self.labels_path.open("r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]

        return [
            "Grade_A_Premium",
            "Grade_B_Good",
            "Grade_C_Standard",
            "Grade_D_Defective",
        ]

    def _load_model(self):
        if self._model is not None:
            return self._model

        if tf is None or not self.model_path.exists():
            self._model = None
            return None

        self._model = tf.keras.models.load_model(self.model_path, compile=False)
        return self._model

    def _preprocess(self, image_path: Path) -> np.ndarray:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            width, height = img.size
            side = min(width, height)

            left = (width - side) // 2
            top = (height - side) // 2
            img = img.crop((left, top, left + side, top + side)).resize((self.img_size, self.img_size))

            # Training notebook normalizes image arrays with image / 255.0.
            arr = np.array(img, dtype=np.float32) / 255.0
        return np.expand_dims(arr, axis=0)

    def _preprocess_sensor(self, sensor: Dict[str, float]) -> np.ndarray:
        # Keep the exact feature order used in multimodal.ipynb: [mq2, mq135, mq3].
        values = [
            float(sensor["mq2"]),
            float(sensor["mq135"]),
            float(sensor["mq3"]),
        ]
        return np.asarray([values], dtype=np.float32)

    def _ensure_probabilities(self, raw_pred: np.ndarray) -> np.ndarray:
        raw_pred = np.asarray(raw_pred, dtype=np.float32)
        if raw_pred.ndim != 1:
            raise ValueError("Output model harus berupa vektor 1 dimensi.")

        pred_sum = float(np.sum(raw_pred))
        is_prob_vector = bool(np.all(raw_pred >= 0.0) and np.all(raw_pred <= 1.0) and abs(pred_sum - 1.0) < 1e-3)
        if is_prob_vector:
            return raw_pred

        if tf is not None:
            return tf.nn.softmax(raw_pred).numpy()

        shifted = raw_pred - float(np.max(raw_pred))
        exps = np.exp(shifted)
        return exps / float(np.sum(exps))

    def calculate_sensor_metrics(self, sensor: Dict[str, float]) -> Dict[str, object]:
        config = self._sensor_config
        refs = config["refs"]
        weights = config["weights"]
        deviation_multiplier = config["deviation_multiplier"]
        
        categories = config["categories"]
        categories = sorted(categories, key=lambda x: x["min_score"], reverse=True)

        details: Dict[str, Dict[str, float]] = {}
        weighted_score = 0.0
        total_weight = 0.0

        for key, ref in refs.items():
            value = max(float(sensor.get(key, ref)), 0.0)
            deviation_ratio = abs(value - ref) / ref
            deviation_pct = deviation_ratio * 100.0
            sensor_score = max(0.0, min(100.0, 100.0 - (deviation_ratio * deviation_multiplier)))
            weight = weights[key]

            weighted_score += sensor_score * weight
            total_weight += weight

            details[key] = {
                "value": round(value, 2),
                "reference": round(ref, 2),
                "delta": round(value - ref, 2),
                "deviation_pct": round(deviation_pct, 2),
                "score": round(sensor_score, 2),
            }

        aroma_score = weighted_score / total_weight if total_weight else 0.0
        
        category = categories[-1]["label"]
        for cat in categories:
            if aroma_score >= cat["min_score"]:
                category = cat["label"]
                break

        return {
            "aroma_score": round(aroma_score, 2),
            "category": category,
            "details": details,
        }

    def _predict_multimodal(self, image_path: Path, sensor: Dict[str, float]) -> Dict[str, float]:
        model = self._load_model()
        if model is None:
            raise ValueError(
                "Model belum siap. Pastikan TensorFlow terinstall dan file model dapat dibaca: "
                f"{self.model_path}"
            )

        image_batch = self._preprocess(image_path)
        sensor_batch = self._preprocess_sensor(sensor)

        if len(getattr(model, "inputs", [])) > 1:
            raw_pred = model.predict([image_batch, sensor_batch], verbose=0)[0]
        else:
            raw_pred = model.predict(image_batch, verbose=0)[0]

        if len(raw_pred) != len(self._labels):
            raise ValueError("Jumlah output model tidak cocok dengan jumlah label.")

        probs = self._ensure_probabilities(raw_pred)
        return {label: float(prob) for label, prob in zip(self._labels, probs)}

    def predict(self, image_path: Path, sensor: Dict[str, float]) -> Dict[str, object]:
        probs = self._predict_multimodal(image_path, sensor)
        top_label = max(probs, key=probs.get)
        top_conf = probs[top_label]

        sensor_analysis = self.calculate_sensor_metrics(sensor)
        aroma_score = float(sensor_analysis["aroma_score"])

        result = PredictionResult(
            grade_label=top_label,
            model_confidence=round(top_conf * 100.0, 2),
            aroma_score=round(aroma_score, 2),
            sensor_analysis=sensor_analysis,
            probabilities={k: round(v * 100.0, 2) for k, v in probs.items()},
            model_ready=self._model is not None,
        )

        return {
            "grade_label": result.grade_label,
            "model_confidence": result.model_confidence,
            "aroma_score": result.aroma_score,
            "sensor_analysis": result.sensor_analysis,
            "probabilities": result.probabilities,
            "model_ready": result.model_ready,
        }
