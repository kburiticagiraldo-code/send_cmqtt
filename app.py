import json

import paho.mqtt.client as paho
import streamlit as st

BROKER = "157.230.214.127"
PORT = 1883
CLIENT_ID = "Stiv_ken"
TOPIC_ACT = "kbgt"        # encendido / apagado
TOPIC_ANALOG = "tgbsk"    # velocidad (0 a 100)

st.set_page_config(page_title="MQTT Control", page_icon="🌀", layout="centered")

CSS = """
<style>
.card{border-radius:24px;padding:28px 20px 22px;text-align:center;margin:8px 0 18px;
 background:linear-gradient(160deg,#eef2ff 0%,#e0f2fe 100%);color:#1e293b;
 border:1px solid #c7d2fe;box-shadow:0 10px 30px rgba(99,102,241,.15);}
.card.off{background:linear-gradient(160deg,#f1f5f9 0%,#e2e8f0 100%);border-color:#cbd5e1;box-shadow:none;}
.chip{display:inline-block;padding:4px 12px;border-radius:999px;font-size:.8rem;font-weight:600;
 background:#c7d2fe;color:#3730a3;}
.card.off .chip{background:#cbd5e1;color:#475569;}
.fan{position:relative;width:170px;height:170px;margin:18px auto 10px;border-radius:50%;
 border:6px solid #a5b4fc;background:radial-gradient(circle,#ffffff 0%,#eef2ff 100%);}
.card.off .fan{border-color:#cbd5e1;}
.blades{position:absolute;top:0;right:0;bottom:0;left:0;animation:giro 1s linear infinite;}
.blade{position:absolute;left:50%;top:50%;width:46px;height:68px;margin-left:-23px;margin-top:-68px;
 border-radius:50% 50% 25% 25% / 85% 85% 15% 15%;background:linear-gradient(180deg,#6366f1,#818cf8);
 transform-origin:50% 100%;opacity:.92;}
.card.off .blade{background:#94a3b8;}
.b1{transform:rotate(0deg);} .b2{transform:rotate(90deg);}
.b3{transform:rotate(180deg);} .b4{transform:rotate(270deg);}
.hub{position:absolute;left:50%;top:50%;width:26px;height:26px;margin:-13px 0 0 -13px;
 border-radius:50%;background:#312e81;}
.card.off .hub{background:#64748b;}
.num{font-size:3rem;font-weight:800;line-height:1;}
.pct{font-size:1.2rem;font-weight:600;margin-left:2px;color:#6366f1;}
.nivel{font-size:.85rem;color:#475569;margin:4px 0 12px;letter-spacing:.08em;text-transform:uppercase;}
.barra{height:8px;border-radius:999px;background:#c7d2fe;overflow:hidden;max-width:260px;margin:0 auto;}
.barra div{height:100%;background:linear-gradient(90deg,#6366f1,#38bdf8);border-radius:999px;transition:width .3s;}
@keyframes giro{to{transform:rotate(360deg);}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# Estado inicial
st.session_state.setdefault("power", False)
st.session_state.setdefault("speed", 50)
st.session_state.setdefault("ultimo", "")
st.session_state.setdefault("error", "")


def crear_cliente():
    try:
        return paho.Client(paho.CallbackAPIVersion.VERSION2, CLIENT_ID)
    except AttributeError:  # paho-mqtt 1.x
        return paho.Client(CLIENT_ID)


def enviar(topico, payload):
    """Publica un mensaje JSON por MQTT."""
    try:
        client = crear_cliente()
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        info = client.publish(topico, json.dumps(payload))
        info.wait_for_publish(timeout=3)
        client.loop_stop()
        client.disconnect()
        st.session_state.ultimo = f"{topico} → {json.dumps(payload)}"
        st.session_state.error = ""
    except Exception as e:
        st.session_state.error = f"No se pudo conectar al broker: {e}"


def cambiar_power():
    enviar(TOPIC_ACT, {"Act1": "ON" if st.session_state.power else "OFF"})


def cambiar_speed():
    enviar(TOPIC_ANALOG, {"Analog": float(st.session_state.speed)})


# ---------- Interfaz ----------
st.title("MQTT Control")
st.caption("Ventilador · envía el encendido y la velocidad a tu dispositivo por MQTT")

power = st.session_state.power
speed = st.session_state.speed if power else 0
girando = power and speed > 0
duracion = 2.0 - 1.75 * speed / 100

if not power:
    nivel = "Apagado"
elif speed == 0:
    nivel = "Detenido"
elif speed < 34:
    nivel = "Suave"
elif speed < 67:
    nivel = "Media"
else:
    nivel = "Turbo"

tarjeta = "".join([
    f'<div class="card {"on" if power else "off"}">',
    f'<span class="chip">{"● Encendido" if power else "○ Apagado"}</span>',
    '<div class="fan">',
    f'<div class="blades" style="animation-duration:{duracion:.2f}s;'
    f'animation-play-state:{"running" if girando else "paused"};">',
    '<span class="blade b1"></span><span class="blade b2"></span>',
    '<span class="blade b3"></span><span class="blade b4"></span>',
    '</div><div class="hub"></div></div>',
    f'<div><span class="num">{speed}</span><span class="pct">%</span></div>',
    f'<div class="nivel">{nivel}</div>',
    f'<div class="barra"><div style="width:{speed}%"></div></div>',
    '</div>',
])
st.markdown(tarjeta, unsafe_allow_html=True)

st.toggle("Encender ventilador", key="power", on_change=cambiar_power)
st.slider(
    "Velocidad",
    0,
    100,
    step=1,
    key="speed",
    on_change=cambiar_speed,
    disabled=not st.session_state.power,
)

if st.session_state.error:
    st.error(st.session_state.error)
elif st.session_state.ultimo:
    st.caption(f"📡 Último mensaje enviado: `{st.session_state.ultimo}`")
else:
    st.caption("📡 Aún no se ha enviado ninguna orden")

st.caption(f"Broker {BROKER}:{PORT} · tópicos: {TOPIC_ACT} (encendido) y {TOPIC_ANALOG} (velocidad)")
