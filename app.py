import streamlit as st
import paho.mqtt.client as mqtt
import pickle
import time

# ===========================
# LOAD MODEL
# ===========================
model = pickle.load(open("model.pkl", "rb"))

# ===========================
# MQTT CONFIG
# ===========================
MQTT_BROKER = "broker.emqx.io"
SENSOR_TOPIC = "Iot/IgniteLogic/sensor"
OUTPUT_TOPIC = "Iot/IgniteLogic/output"

latest_sensor_data = {"temperature": None, "humidity": None, "light": None}
latest_output = None

# ===========================
# MQTT CALLBACKS
# ===========================
def on_connect(client, userdata, flags, rc):
    client.subscribe(SENSOR_TOPIC)
    client.subscribe(OUTPUT_TOPIC)

def on_message(client, userdata, msg):
    global latest_sensor_data, latest_output

    payload = msg.payload.decode()
    topic = msg.topic

    if topic == SENSOR_TOPIC:
        try:
            t, h, l = payload.split(",")
            latest_sensor_data["temperature"] = float(t)
            latest_sensor_data["humidity"] = float(h)
            latest_sensor_data["light"] = float(l)
        except:
            pass

    if topic == OUTPUT_TOPIC:
        latest_output = payload

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, 1883)
client.loop_start()

# ===========================
# STREAMLIT UI
# ===========================
st.title("🔥 IoT + Machine Learning Dashboard")
st.write("Real-time monitoring menggunakan ESP32 + MQTT + ML")

sensor_box = st.empty()
prediction_box = st.empty()
output_box = st.empty()

# ===========================
# LOOP TAMPILKAN DATA
# ===========================
while True:
    t = latest_sensor_data["temperature"]
    h = latest_sensor_data["humidity"]
    l = latest_sensor_data["light"]

    # ========== TAMPILKAN SENSOR ==========
    if t is not None:
        sensor_box.info(
            f"""
            **Sensor Data (ESP32):**  
            🔥 Suhu: `{t}`  
            💧 Lembap: `{h}`  
            💡 Cahaya: `{l}`  
            """
        )

        # ========== ML PREDIKSI ==========
        input_data = [[t, h, l]]
        pred = model.predict(input_data)[0]

        # ========== ALERT WARNA ==========
        if pred == "Aman":
            prediction_box.success("🟢 Status: AMAN")
        else:
            prediction_box.error("🔴 Status: TIDAK AMAN")

    else:
        sensor_box.warning("Menunggu data dari ESP32...")

    # ========== OUTPUT TOPIC STATUS ==========
    if latest_output is not None:
        if latest_output == "Aman":
            output_box.success("🟢 Lampu Aman (Hijau)")
        else:
            output_box.error("🔴 Lampu Tidak Aman (Merah)")
    else:
        output_box.info("Menunggu data output dari ESP32...")

    time.sleep(0.5)
