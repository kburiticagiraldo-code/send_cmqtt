import html
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
.stApp{
  background:
    radial-gradient(circle at 15% 0%, rgba(99,102,241,.45) 0%, transparent 45%),
    radial-gradient(circle at 95% 15%, rgba(14,165,233,.35) 0%, transparent 40%),
    #0b1020;
  background-attachment:fixed;
}
[data-testid="stHeader"]{background:transparent;}
footer{visibility:hidden;}
.block-container{max-width:560px;padding-top:2.2rem;}

/* Encabezado */
.hero{text-align:center;margin-bottom:18px;}
.badge{display:inline-block;padding:5px 14px;border-radius:999px;font-size:.78rem;font-weight:600;
 letter-spacing:.06em;color:#a5f3fc;background:rgba(34,211,238,.12);border:1px solid rgba(34,211,238,.35);}
.hero .titulo{font-size:2.5rem;font-weight:800;margin:10px 0 2px;color:#f8fafc;line-height:1.1;}
.hero .titulo span{background:linear-gradient(90deg,#22d3ee,#a78bfa);-webkit-background-clip:text;
 background-clip:text;color:transparent;}
.hero .sub{color:#94a3b8;font-size:.95rem;}

/* Tarjeta */
.card{position:relative;overflow:hidden;text-align:center;padding:26px 20px 24px;margin:6px 0 22px;
 border-radius:28px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);
 backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);box-shadow:0 20px 50px rgba(0,0,0,.45);
 --c:#22d3ee;--c1:#22d3ee;--c2:#a78bfa;}
.card.off{--c:#000;--c1:#475569;--c2:#64748b;}
.chip{display:inline-flex;align-items:center;gap:8px;padding:5px 14px;border-radius:999px;font-size:.8rem;
 font-weight:600;color:#bbf7d0;background:rgba(34,197,94,.14);border:1px solid rgba(34,197,94,.4);}
.chip i{width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 10px #22c55e;}
.card.off .chip{color:#cbd5e1;background:rgba(148,163,184,.12);border-color:rgba(148,163,184,.3);}
.card.off .chip i{background:#64748b;box-shadow:none;}

/* Ventilador */
.fan{position:relative;width:200px;height:200px;margin:42px auto 34px;border-radius:50%;
 background:radial-gradient(circle,#0f172a 0%,#1e293b 100%);border:4px solid rgba(148,163,184,.5);
 box-shadow:inset 0 0 30px rgba(0,0,0,.65),0 0 var(--glow) var(--c);}
.fan::after{content:"";position:absolute;top:0;right:0;bottom:0;left:0;border-radius:50%;z-index:3;
 pointer-events:none;
 background:repeating-conic-gradient(transparent 0deg 14deg,rgba(148,163,184,.16) 14deg 15deg),
 repeating-radial-gradient(circle,transparent 0 22px,rgba(148,163,184,.2) 22px 24px);}
.onda{position:absolute;top:0;right:0;bottom:0;left:0;border-radius:50%;border:2px solid var(--c);
 opacity:0;animation:onda var(--t) ease-out infinite;}
.onda.o2{animation-delay:calc(var(--t) / 2);}
.card.off .onda{display:none;}
.blades{position:absolute;top:0;right:0;bottom:0;left:0;z-index:2;animation:giro 1s linear infinite;}
.blade{position:absolute;left:50%;top:50%;width:54px;height:80px;margin-left:-27px;margin-top:-80px;
 border-radius:55% 55% 30% 30% / 90% 90% 20% 20%;background:linear-gradient(160deg,var(--c1),var(--c2));
 transform-origin:50% 100%;box-shadow:inset -4px 0 8px rgba(0,0,0,.25);opacity:.95;}
.b1{transform:rotate(0deg) skewX(-10deg);}  .b2{transform:rotate(72deg) skewX(-10deg);}
.b3{transform:rotate(144deg) skewX(-10deg);} .b4{transform:rotate(216deg) skewX(-10deg);}
.b5{transform:rotate(288deg) skewX(-10deg);}
.hub{position:absolute;left:50%;top:50%;width:38px;height:38px;margin:-19px 0 0 -19px;border-radius:50%;
 z-index:4;background:radial-gradient(circle at 35% 30%,#e2e8f0,#475569);border:3px solid #0f172a;}
@keyframes giro{to{transform:rotate(360deg);}}
@keyframes onda{0%{transform:scale(1);opacity:.55;}100%{transform:scale(1.5);opacity:0;}}

/* Lectura */
.num{font-size:3.8rem;font-weight:800;line-height:1;background:linear-gradient(90deg,#22d3ee,#a78bfa);
 -webkit-background-clip:text;background-clip:text;color:transparent;}
.pct{font-size:1.3rem;font-weight:700;margin-left:3px;color:#94a3b8;}
.niveles{display:flex;justify-content:center;gap:8px;margin:14px 0 16px;}
.niveles span{padding:4px 14px;border-radius:999px;font-size:.75rem;font-weight:600;letter-spacing:.06em;
 text-transform:uppercase;color:#64748b;border:1px solid rgba(148,163,184,.25);}
.niveles span.act{color:#0b1020;background:linear-gradient(90deg,#22d3ee,#a78bfa);border-color:transparent;}
.barra{height:8px;border-radius:999px;background:rgba(148,163,184,.2);overflow:hidden;max-width:280px;margin:0 auto;}
.barra div{height:100%;border-radius:999px;background:linear-gradient(90deg,#22d3ee,#a78bfa);transition:width .3s;}

/* Controles */
.panel{margin:4px 0 8px;font-size:.8rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#94a3b8;}
.stButton>button{width:100%;border-radius:14px;padding:.6rem 0;color:#e2e8f0;transition:all .2s;
 background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.15);}
.stButton>button:hover:not(:disabled){border-color:#22d3ee;color:#fff;box-shadow:0 0 16px rgba(34,211,238,.35);}
.stButton>button:disabled{opacity:.4;}

/* Estado */
.estado{margin-top:14px;padding:10px 14px;border-radius:14px;font-size:.82rem;color:#cbd5e1;
 background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);word-break:break-all;}
.estado.err{color:#fecaca;border-color:rgba(239,68,68,.5);background:rgba(239,68,68,.1);}
.pie{text-align:center;color:#64748b;font-size:.75rem;margin-top:16px;}
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


def preset(valor):
    st.session_state.speed = valor
    cambiar_speed()


def nivel_de(power, speed):
    if not power:
        return "Apagado"
    if speed == 0:
        return "Detenido"
    if speed < 34:
        return "Suave"
    if speed < 67:
        return "Media"
    return "Turbo"


def render_tarjeta(power, speed):
    girando = power and speed > 0
    giro = 2.0 - 1.75 * speed / 100
    onda = max(0.8, 2.4 - speed * 0.016)
    glow = 10 + speed * 0.45
    nivel = nivel_de(power, speed)
    pills = "".join(
        f'<span class="{"act" if nivel == n else ""}">{n}</span>' for n in ("Suave", "Media", "Turbo")
    )
    return "".join([
        f'<div class="card {"on" if power else "off"}" style="--glow:{glow:.0f}px;--t:{onda:.2f}s;">',
        f'<span class="chip"><i></i>{"Encendido" if power else "Apagado"}</span>',
        '<div class="fan"><span class="onda"></span><span class="onda o2"></span>',
        f'<div class="blades" style="animation-duration:{giro:.2f}s;'
        f'animation-play-state:{"running" if girando else "paused"};">',
        '<span class="blade b1"></span><span class="blade b2"></span><span class="blade b3"></span>',
        '<span class="blade b4"></span><span class="blade b5"></span></div>',
        '<div class="hub"></div></div>',
        f'<div><span class="num">{speed}</span><span class="pct">%</span></div>',
        f'<div class="niveles">{pills}</div>',
        f'<div class="barra"><div style="width:{speed}%"></div></div>',
        '</div>',
    ])


# ---------- Interfaz ----------
st.markdown(
    '<div class="hero"><span class="badge">🌀 VENTILADOR · MQTT</span>'
    '<div class="titulo">MQTT <span>Control</span></div>'
    '<div class="sub">Enciende y regula tu ventilador en tiempo real</div></div>',
    unsafe_allow_html=True,
)

power = st.session_state.power
speed = st.session_state.speed if power else 0
st.markdown(render_tarjeta(power, speed), unsafe_allow_html=True)

st.markdown('<div class="panel">Panel de control</div>', unsafe_allow_html=True)
st.toggle("Encender ventilador", key="power", on_change=cambiar_power)

b1, b2, b3 = st.columns(3)
b1.button("🍃 Suave", on_click=preset, args=(25,), disabled=not power)
b2.button("💨 Media", on_click=preset, args=(60,), disabled=not power)
b3.button("🌪️ Turbo", on_click=preset, args=(100,), disabled=not power)

st.slider("Velocidad", 0, 100, step=1, key="speed", on_change=cambiar_speed, disabled=not power)

if st.session_state.error:
    st.markdown(f'<div class="estado err">⚠️ {html.escape(st.session_state.error)}</div>', unsafe_allow_html=True)
elif st.session_state.ultimo:
    st.markdown(
        f'<div class="estado">📡 Último mensaje enviado: <code>{html.escape(st.session_state.ultimo)}</code></div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown('<div class="estado">📡 Aún no se ha enviado ninguna orden</div>', unsafe_allow_html=True)

st.markdown(
    f'<div class="pie">Broker {BROKER}:{PORT} · tópicos {TOPIC_ACT} (encendido) y {TOPIC_ANALOG} (velocidad)</div>',
    unsafe_allow_html=True,
)
