import os
import time
import random
import pandas as pd
import threading
from pythonosc.udp_client import SimpleUDPClient

# === CONFIG ========================
DATASET_PATH = ""
OSC_IP = ""
OSC_PORT = 8000
SAMPLE_RATE = 200  # Hz
INTERACTIONS = ["Baseline", "T1", "T2", "T3"]

# === OSC CLIENT ====================
osc_client = SimpleUDPClient(OSC_IP, OSC_PORT)

# === INTERACTION STATE =============
current_interaction = "Baseline"
interaction_lock = threading.Lock()

def interaction_input_loop():
    global current_interaction
    while True:
        new_type = input("Enter interaction type (Baseline/T1/T2/T3): ").strip()
        if new_type in INTERACTIONS:
            with interaction_lock:
                current_interaction = new_type
        else:
            print("Invalid type. Choose from Baseline, T1, T2, T3.")

# === CSV SENDER ====================
def load_random_csv(interaction):
    folder = os.path.join(DATASET_PATH, interaction)
    files = [f for f in os.listdir(folder) if f.endswith(".csv")]
    if not files:
        print(f"No CSV files in {folder}")
        return None
    chosen = random.choice(files)
    path = os.path.join(folder, chosen)
    print(f"📄 Using file: {path}")
    return pd.read_csv(path)

def send_lms_osc(row, interaction):
    osc_client.send_message("/interaction", interaction)
    osc_client.send_message("/norm", float(row['normalized_lms']))
    osc_client.send_message("/rate", float(row['rate_lms']))
    osc_client.send_message("/env", float(row['envelope_lms']))
    osc_client.send_message("/mean", float(row['mean_lms']))
    osc_client.send_message("/var", float(row['variance_lms']))
    osc_client.send_message("/energy", float(row['energy_lms']))

# === MAIN LOOP =====================
if __name__ == "__main__":
    print("CSV Plant Emulator (OSC + Continuous Streaming)")

    # Start input thread
    threading.Thread(target=interaction_input_loop, daemon=True).start()

    while True:
        with interaction_lock:
            interaction_to_run = current_interaction

        df = load_random_csv(interaction_to_run)
        if df is None:
            time.sleep(1)
            continue

        for _, row in df.iterrows():
            send_lms_osc(row, interaction_to_run)
            time.sleep(1.0 / SAMPLE_RATE)

        # Check again before loading new file
        with interaction_lock:
            interaction_to_run = current_interaction
