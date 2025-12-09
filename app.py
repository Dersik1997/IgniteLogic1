import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import time
from paho.mqtt import client as mqtt_client
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------
# LOAD MODEL
# --------------------------------------------
model = joblib.load("model.pkl")

# --------------------------------------------
# MQTT CONFIG
# --------------------------------------------
BROKER = "broker.emqx.io"
PORT = 1883
TOPIC_SENSOR = "Iot/IgniteLogic/sensor"
TOPIC_OUTPUT = "Iot/IgniteLogic/output"
CLIENT_ID = "streamlit-dashboard-001"

latest_sensor = {"temp": None, "hum": None, "light": None, "label": "-"}

# --------------------------------------------
# MQTT CALLBACK HANDLING
# --------------------------------------------
def on_message(client, userdata, msg):
    global latest_sensor
    try:
        data = json.loads(msg.payload.decode())
        latest_sensor.update(data)
    except:
        pass

def connect_mqtt():
    client = mqtt_client.Client(CLIENT_ID)
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.subscribe(TOPIC_SENSOR)
    return client

client = connect_mqtt()
client.loop_start()

# --------------------------------------------
# STREAMLIT UI
# --------------------------------------------
st.set_page_config(page_title="IgniteLogic Dashboard", layout="centered")

st.title("🔥 IgniteLogic - IoT + Machine Learning Dashboard")

# auto-refresh setiap 2 detik
st_autorefresh(interval=2000, key="datastream")

st.subheader("📡 Data Sensor Terbaru")

temp = latest_sensor.get("temp")
hum = latest_sensor.get("hum")
light = latest_sensor.get("light")

col1, col2, col3 = st.columns(3)
col1.metric("Temperature (°C)", temp)
col2.metric("Humidity (%)", hum)
col3.metric("Light", light)

# --------------------------------------------
# ML PREDICTION
# --------------------------------------------
if temp is not None and hum is not None and light is not None:

    input_data = np.array([[temp, hum, light]])
    pred = model.predict(input_data)[0]

    st.subheader("🤖 ML Prediction Output")

    if pred == "Aman":
        st.success("🟢 AMAN")
        color = "Green"
    else:
        st.error("🔴 TIDAK AMAN")
        color = "Red"

    # Publish prediction ke ESP32
    client.publish(TOPIC_OUTPUT, pred)

    st.write(f"Prediction sent to ESP32 → **{pred}**")

else:
    st.warning("Menunggu data dari ESP32...")

st.write("---")
st.caption("Connected to EMQX MQTT Broker")
