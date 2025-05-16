import numpy as np
import joblib
import pandas as pd
import time
from collections import deque
from pymaxmusic import pymax

class Classifier:
    def __init__(self):
        self.FRAME_SIZE = 10000
        self.FFT_BINS = 40
        self.BASELINE_BOOST = 2
        self.CONFIDENCE_THRESHOLD = 0.70

        self.bundle = joblib.load("optimized_model.pkl")
        self.model = self.bundle["model"]
        self.encoder = self.bundle["encoder"]
        self.scaler = self.bundle["scaler"]
        self.baseline_idx = self.encoder.transform(["Baseline"])[0]

        self.buffer_norm = deque(maxlen=self.FRAME_SIZE)
        self.buffer_rate = deque(maxlen=self.FRAME_SIZE)
        self.buffer_env = deque(maxlen=self.FRAME_SIZE)
        self.buffer_mean = deque(maxlen=self.FRAME_SIZE)
        self.buffer_var = deque(maxlen=self.FRAME_SIZE)
        self.buffer_energy = deque(maxlen=self.FRAME_SIZE)

        # === Timer for output rate limiting ===
        self.last_output_time = 0  # timestamp of last interaction output
        self.OUTPUT_INTERVAL = 1.0  # seconds between outputs

    def input(self, norm, rate, env, mean, var, energy):
        self.buffer_norm.append(norm)
        self.buffer_rate.append(rate)
        self.buffer_env.append(env)
        self.buffer_mean.append(mean)
        self.buffer_var.append(var)
        self.buffer_energy.append(energy)

        if len(self.buffer_norm) < self.FRAME_SIZE:
            return None  # wait until buffer is full

        current_time = time.time()
        if current_time - self.last_output_time >= self.OUTPUT_INTERVAL:
            label = self.classify_frame()
            self.last_output_time = current_time
            return label
        else:
            return None  # skip output until enough time has passed

    def classify_frame(self):
        norm_arr = np.array(self.buffer_norm)

        feats = {
            'rate_raw_mean': np.mean(self.buffer_rate),
            'envelope_lms_mean': np.mean(self.buffer_env),
            'variance_lms_mean': np.mean(self.buffer_var),
            'energy_raw_mean': np.mean(self.buffer_energy),
            'mean_lms_mean': np.mean(self.buffer_mean),
        }

        fft = self.compute_fft_bins(norm_arr)
        for i in range(self.FFT_BINS):
            feats[f'fft_lms_{i}'] = fft[i]

        X = pd.DataFrame([feats], columns=self.scaler.feature_names_in_)
        X_scaled = self.scaler.transform(X)
        y_prob = self.model.predict_proba(X_scaled)[0]
        y_prob[self.baseline_idx] *= self.BASELINE_BOOST
        y_prob /= np.sum(y_prob)

        y_pred = np.argmax(y_prob)
        label = self.encoder.inverse_transform([y_pred])[0]
        confidence = y_prob[y_pred]

        if confidence >= self.CONFIDENCE_THRESHOLD or label == "Baseline":
            return label
        else:
            return "Baseline"

    def compute_fft_bins(self, signal, bins=40):
        fft = np.fft.rfft(signal * np.hanning(len(signal)), n=256)
        mag = np.abs(fft)
        grouped = np.mean(mag[:bins * (len(mag) // bins)].reshape(bins, -1), axis=1)
        return grouped

# === PyMax bootstrapping ===
pymax.open_pymax()
pymax.add_class("classifier", Classifier)
pymax.run_pymax()
