"""
============================================================
 OunceAI Bridge — Balança HX711 + Câmera YOLO11 → PostgreSQL
============================================================
 Modelo customizado: model_yolo11_0.1.pt
 Classes treinadas (nc=3):
   0 → Caixa de Leite
   1 → Coca Cola
   2 → Guarana

 Orquestra a leitura serial da balança (ESP32/HX711) e as
 detecções YOLO11, correlacionando-as pelo id_sensor dentro
 de uma janela temporal e gravando eventos bimodais completos
 na tabela fato_auditoria_bimodal.

 Uso rápido:
   python ounce_bridge.py

 Dependências:
   pip install pyserial ultralytics opencv-python
               psycopg2-binary python-dotenv numpy
============================================================
"""

import serial
import serial.tools.list_ports
import cv2
import psycopg2
import psycopg2.extras
import numpy as np
import time
import logging
import sys
import os
import threading
import queue
from datetime import datetime
from collections import deque
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

try:
    from ultralytics import YOLO
except ImportError:
    print("❌ Instale o ultralytics: pip install ultralytics")
    sys.exit(1)

load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURAÇÕES CENTRALIZADAS
# ─────────────────────────────────────────────
CONFIG = {
    # ── Serial ──────────────────────────────
    "SERIAL_PORT":   os.getenv("SERIAL_PORT", "COM3"),
    "BAUD_RATE":     int(os.getenv("BAUD_RATE", "115200")),
    "ID_SENSOR":     int(os.getenv("ID_SENSOR", "1")),

    # ── YOLO11 / Câmera ────────────────
    "YOLO_MODEL":    os.getenv("YOLO_MODEL_PATH", "model_yolo11_0.1.pt"),
    "YOLO_CONF":     float(os.getenv("YOLO_CONFIDENCE", "0.50")),  # 50% mínimo
    "YOLO_IOU":      float(os.getenv("YOLO_IOU", "0.45")),
    "CAMERA_INDEX":  int(os.getenv("CAMERA_INDEX", "0")),
    "FRAME_W":       int(os.getenv("FRAME_WIDTH", "640")),
    "FRAME_H":       int(os.getenv("FRAME_HEIGHT", "480")),
    "MOSTRAR_JANELA": os.getenv("MOSTRAR_JANELA", "true").lower() == "true",

    # Classes do modelo customizado (nc=3) — NÃO ALTERE A ORDEM
    # Devem bater exatamente com nome_produto na dim_produto
    "CLASSES_MODELO": {
        0: "Leite Italac 1L",
        1: "Coca Cola Lata 350",
        2: "Guarana Lata 350",
    },

    # Cores BGR fixas por produto para o overlay
    "CORES_PRODUTO": {
        "Leite Italac 1L":    (30,  200, 255),   # Amarelo/Ouro
        "Coca Cola Lata 350": (0,   30,  210),   # Vermelho
        "Guarana Lata 350":   (30,  180,  60),   # Verde
    },

    # ── PostgreSQL ───────────────────
    "PG_HOST":  os.getenv("PG_HOST",  "localhost"),
    "PG_PORT":  int(os.getenv("PG_PORT", "5432")),
    "PG_DB":    os.getenv("PG_DB",    "ounceai_db"),
    "PG_USER":  os.getenv("PG_USER",  "ounceAI"),
    "PG_PASS":  os.getenv("PG_PASS",  "OnçaPintuda"),

    # ── Comportamento ─────────────────
    "CORRELACAO_JANELA_S":      3.0,   # janela temporal p/ correlacionar balança ↔ câmera
    "MIN_INTERVALO_EVENTO_S":   2.0,   # evita eventos duplicados
    "RECONNECT_DELAY_S":        5,
}

# ─────────────────────────────────────────────
# LOGGER
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bridge.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("ounce.bridge")

# ─────────────────────────────────────────────
# ESTADO COMPARTILHADO (thread-safe)
# ─────────────────────────────────────────────
lock_estado = threading.Lock()

# Último evento de cada sensor: {id_sensor: {"peso", "variacao", "ts"}}
ultimas_leituras_balanca: dict[int, dict] = {}

# Fila de eventos bimodais prontos para gravar
evento_queue: queue.Queue = queue.Queue(maxsize=300)

# ─────────────────────────────────────────────
# FUNÇÕES POSTGRES
# ─────────────────────────────────────────────

def conectar_pg() -> psycopg2.extensions.connection:
    while True:
        try:
            conn = psycopg2.connect(
                host=CONFIG["PG_HOST"], port=CONFIG["PG_PORT"],
                dbname=CONFIG["PG_DB"], user=CONFIG["PG_USER"],
                password=CONFIG["PG_PASS"], connect_timeout=10,
            )
            conn.autocommit = False
            log.info("✅ PostgreSQL conectado.")
            return conn
        except psycopg2.OperationalError as e:
            log.error(f"❌ PG: {e}")
            time.sleep(CONFIG["RECONNECT_DELAY_S"])


def garantir_schema(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS leituras_balanca (
                id_leitura      SERIAL PRIMARY KEY,
                id_sensor_hx711 INT NOT NULL,
                peso            DECIMAL(10,2) NOT NULL,
                variacao        DECIMAL(10,2) NOT NULL,
                data_leitura    TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.commit()


def obter_fk_produto(conn, nome: str) -> int | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT sk_produto FROM dim_produto WHERE LOWER(nome_produto)=LOWER(%s) LIMIT 1",
            (nome,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def obter_fk_hardware(conn, id_sensor: int) -> int | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT sk_hardware FROM dim_hardware WHERE id_sensor_hx711=%s LIMIT 1",
            (id_sensor,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def gerar_sk_tempo(conn, ts: datetime) -> int:
    sk = int(ts.strftime("%Y%m%d%H"))
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM dim_tempo WHERE sk_tempo=%s", (sk,))
        if not cur.fetchone():
            dia_nomes = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
            dia_semana = dia_nomes[ts.weekday()]
            h = ts.hour
            turno = "Manhã" if 6<=h<12 else "Tarde" if 12<=h<18 else "Noite" if 18<=h<22 else "Madrugada"
            cur.execute("""
                INSERT INTO dim_tempo(sk_tempo,data_completa,ano,mes,dia,hora,minuto,dia_semana,turno)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(sk_tempo) DO NOTHING
            """, (sk,ts,ts.year,ts.month,ts.day,ts.hour,ts.minute,dia_semana,turno))
    return sk


def regra_auditoria(conf: float, delta: float, esperado: float, preco: float):
    """Retorna (status, receita_protegida, perda_estimada)."""
    tolerancia = esperado * 0.10 if esperado > 0 else 20.0
    if conf >= 0.80 and abs(delta - esperado) <= tolerancia:
        return "Validado", preco, 0.0
    if not (conf >= 0.45) and delta > 10:
        return "Suspeito", 0.0, preco
    if conf >= 0.45 and abs(delta) <= 5:
        return "Divergência Fantasma", 0.0, 0.0
    return "Reposição", 0.0, 0.0


def gravar_evento(conn, evento: dict):
    """Grava leitura bruta na balança E evento na fato."""

    ts        = evento["timestamp"]
    id_sensor = evento["id_sensor"]
    peso      = evento.get("peso", 0.0)
    variacao  = evento.get("variacao", 0.0)
    classe    = evento.get("classe", "desconhecido")
    conf      = evento.get("confianca", 0.0)
    delta     = abs(variacao)

    # 1. Grava leitura bruta
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO leituras_balanca(id_sensor_hx711,peso,variacao,data_leitura) VALUES(%s,%s,%s,%s)",
            (id_sensor, peso, variacao, ts),
        )

    # 2. Grava fato (somente se há detecção YOLO válida)
    if conf > 0:
        fk_produto  = obter_fk_produto(conn, classe)
        fk_hardware = obter_fk_hardware(conn, id_sensor)
        fk_tempo    = gerar_sk_tempo(conn, ts)

        if fk_produto and fk_hardware:
            # Busca preço/massa nominal para regras
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT massa_nominal_gramas, preco_unitario FROM dim_produto WHERE sk_produto=%s",
                    (fk_produto,),
                )
                row = cur.fetchone()
                massa_nom = float(row[0]) if row else 0.0
                preco     = float(row[1]) if row else 0.0

            status, receita, perda = regra_auditoria(conf, delta, massa_nom, preco)
            dwell = max(1, int(evento.get("dwell_time", 2)))

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO fato_auditoria_bimodal
                        (fk_produto,fk_hardware,fk_tempo,
                         delta_massa_gramas,dwell_time_segundos,
                         yolo_confidence_score,ia_detectou,
                         status_auditoria,receita_protegida,perda_estimada)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    fk_produto, fk_hardware, fk_tempo,
                    round(delta,2), dwell,
                    round(conf,4), True,
                    status, round(receita,2), round(perda,2),
                ))

            log.info(
                f"✅ EVENTO BIMODAL | {classe} | conf={conf:.1%} | "
                f"Δ={delta:.0f}g | balança=#{id_sensor} | {status}"
            )
        else:
            log.warning(f"⚠️  Produto '{classe}' ou sensor #{id_sensor} não cadastrado.")

    conn.commit()


# ─────────────────────────────────────────────
# THREAD 1: Leitura Serial (Balança)
# ─────────────────────────────────────────────

def thread_serial():
    id_sensor = CONFIG["ID_SENSOR"]
    log.info(f"🔌 Aguardando porta serial {CONFIG['SERIAL_PORT']}...")

    while True:
        try:
            with serial.Serial(CONFIG["SERIAL_PORT"], CONFIG["BAUD_RATE"], timeout=2) as ser:
                log.info(f"✅ Porta serial {CONFIG['SERIAL_PORT']} aberta.")
                while True:
                    linha = ser.readline()
                    if not linha:
                        continue
                    decoded = linha.decode("utf-8", errors="ignore").strip()
                    if "," not in decoded:
                        continue
                    try:
                        parts = decoded.split(",")
                        if len(parts) == 3:
                            sensor_lido = int(parts[0].strip())
                            peso        = float(parts[1].strip())
                            variacao    = float(parts[2].strip())
                        elif len(parts) == 2:
                            sensor_lido = id_sensor
                            peso        = float(parts[0].strip())
                            variacao    = float(parts[1].strip())
                        else:
                            continue

                        with lock_estado:
                            ultimas_leituras_balanca[sensor_lido] = {
                                "peso":     peso,
                                "variacao":  variacao,
                                "ts":       time.time(),
                            }
                        log.debug(f"📡 Balança #{sensor_lido}: {peso:.1f}g  Δ={variacao:.1f}g")
                    except (ValueError, IndexError):
                        pass
        except serial.SerialException as e:
            log.error(f"❌ Serial: {e}")
            time.sleep(CONFIG["RECONNECT_DELAY_S"])


# ─────────────────────────────────────────────
# THREAD 2: Câmera YOLO → correlação → fila
# ─────────────────────────────────────────────

def thread_camera():
    import paho.mqtt.client as mqtt
    import json
    
    # Inicia e mantém a conexão MQTT em background
    mqtt_client = mqtt.Client()
    try:
        mqtt_client.connect("broker.hivemq.com", 1883, 60)
        mqtt_client.loop_start()
    except Exception as e:
        pass
    
    # Mapeamento câmera → id_sensor
    cam_idx   = CONFIG["CAMERA_INDEX"]
    id_sensor = CONFIG["ID_SENSOR"]  # simplificado: 1 câmera → 1 sensor

    # Carregar fonte Montserrat
    try:
        font_large = ImageFont.truetype("Montserrat-Medium.ttf", 20)
        font_medium = ImageFont.truetype("Montserrat-Medium.ttf", 16)
    except IOError:
        log.warning("⚠️ Fonte Montserrat não encontrada, usando padrão.")
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()

    log.info(f"📷 Carregando YOLO11: {CONFIG['YOLO_MODEL']}")
    model = YOLO(CONFIG["YOLO_MODEL"])
    # Sobrescreve nomes com o mapeamento PT-BR garantido
    model.model.names = CONFIG["CLASSES_MODELO"]
    log.info(f"✅ YOLO11 pronto. Classes: {CONFIG['CLASSES_MODELO']}")

    cap = cv2.VideoCapture(cam_idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CONFIG["FRAME_W"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG["FRAME_H"])
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        log.error(f"❌ Câmera {cam_idx} inacessível.")
        return

    # Paleta dinâmica de cores
    def cor_classe(nome):
        rng = np.random.default_rng(abs(hash(nome)) % 2**32)
        b, g, r = rng.integers(80, 230, size=3).tolist()
        return (b, g, r)

    ultima_ts_classe: dict[str, float] = {}
    rastreio_camera: dict[str, float] = {}
    fps_count = 0
    fps_ts    = time.time()
    fps_val   = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        results = model.predict(source=frame, conf=CONFIG["YOLO_CONF"],
                                iou=CONFIG["YOLO_IOU"], imgsz=320, verbose=False)

        # Atualiza FPS
        fps_count += 1
        agora = time.time()
        if agora - fps_ts >= 1.0:
            fps_val   = fps_count / (agora - fps_ts)
            fps_count = 0
            fps_ts    = agora

        # ── Processar detecções ──────────────────────
        classes_no_frame = set()

        if results and results[0].boxes is not None:
            boxes     = results[0].boxes.xyxy.cpu().numpy()
            scores    = results[0].boxes.conf.cpu().numpy()
            class_ids = results[0].boxes.cls.cpu().numpy().astype(int)
            names     = results[0].names

            for box, score, cls_id in zip(boxes, scores, class_ids):
                if score < CONFIG["YOLO_CONF"]: continue
                # Mapeamento garantido das classes do modelo customizado
                classe = CONFIG["CLASSES_MODELO"].get(int(cls_id), f"classe_{cls_id}")
                classes_no_frame.add(classe)

                # Throttle por classe
                if agora - ultima_ts_classe.get(classe, 0) < CONFIG["MIN_INTERVALO_EVENTO_S"]:
                    continue
                ultima_ts_classe[classe] = agora

                # Correlacionar com leitura da balança (janela temporal)
                with lock_estado:
                    lb = ultimas_leituras_balanca.get(id_sensor, {})
                    lb_ts = lb.get("ts", 0)
                    peso    = lb.get("peso",    0.0) if (agora - lb_ts) <= CONFIG["CORRELACAO_JANELA_S"] else 0.0
                    variacao = lb.get("variacao", 0.0) if peso else 0.0

                evento = {
                    "timestamp":  datetime.now(),
                    "classe":     classe,
                    "classe_id":  int(cls_id),
                    "confianca":  float(score),
                    "id_sensor":  id_sensor,
                    "peso":       peso,
                    "variacao":   variacao,
                    "dwell_time": int(agora - lb_ts) if peso else 1,
                }

                try:
                    evento_queue.put_nowait(evento)
                    log.info(
                        f"🔍 [{int(cls_id)}] {classe} | conf={float(score):.1%} "
                        f"| Δ={abs(variacao):.0f}g | balança=#{id_sensor}"
                    )
                except queue.Full:
                    log.warning("⚠️  Fila de eventos cheia!")

        # --- Rastreio contínuo para MQTT (5 segundos) ---
        for c in list(rastreio_camera.keys()):
            if c not in classes_no_frame:
                del rastreio_camera[c]
                
        for c in classes_no_frame:
            if c not in rastreio_camera:
                rastreio_camera[c] = agora
            elif (agora - rastreio_camera[c]) >= 3.0:
                # Gatilho MQTT
                produto_map = {
                    "Leite Italac 1L": "LEITE",
                    "Coca Cola Lata 350": "COCA",
                    "Guarana Lata 350": "GUARANA"
                }
                alvo = produto_map.get(c)
                if alvo:
                    try:
                        mqtt_client.publish("ounceai/ofertas/trigger", json.dumps({"produto": alvo}))
                        log.info(f"🌐 MQTT: Gatilho enviado para {alvo} (visivel pela camera > 3s)")
                    except Exception as e:
                        log.error(f"❌ Erro MQTT: {e}")
                # Pausa longa para não flodar o painel
                rastreio_camera[c] = agora + 9999.0


        # ── Overlay visual ───────────────────────────
        if CONFIG["MOSTRAR_JANELA"]:
            h, w = frame.shape[:2]

            # Fundo translucido para o HUD superior
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 75), (20, 20, 20), -1)
            # Fundo translucido para o HUD inferior
            cv2.rectangle(overlay, (0, h - 65), (w, h), (20, 20, 20), -1)
            cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

            # Desenhar Bounding Boxes (caixas vazias)
            if results and results[0].boxes is not None:
                for box, score, cls_id in zip(
                    results[0].boxes.xyxy.cpu().numpy(),
                    results[0].boxes.conf.cpu().numpy(),
                    results[0].boxes.cls.cpu().numpy().astype(int),
                ):
                    if score < CONFIG["YOLO_CONF"]:
                        continue
                    classe = CONFIG["CLASSES_MODELO"].get(int(cls_id), f"classe_{cls_id}")
                    x1, y1, x2, y2 = map(int, box)
                    cor = CONFIG["CORES_PRODUTO"].get(classe, (180, 180, 180))
                    cv2.rectangle(frame, (x1, y1), (x2, y2), cor, 2, cv2.LINE_AA)

            # Preparar Pillow para renderizar o texto com a fonte Montserrat
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            draw = ImageDraw.Draw(pil_img)

            # Texto HUD Superior (RGB)
            txt_hud_sup = f"OunceAI Bridge  |  Balança #{id_sensor}  |  {fps_val:.1f} FPS  |  {datetime.now().strftime('%H:%M:%S')}  |  [F] Tela Cheia"
            draw.text((15, 24), txt_hud_sup, font=font_large, fill=(255, 200, 50))

            # Texto das Bounding Boxes
            if results and results[0].boxes is not None:
                for box, score, cls_id in zip(
                    results[0].boxes.xyxy.cpu().numpy(),
                    results[0].boxes.conf.cpu().numpy(),
                    results[0].boxes.cls.cpu().numpy().astype(int),
                ):
                    if score < CONFIG["YOLO_CONF"]:
                        continue
                    classe = CONFIG["CLASSES_MODELO"].get(int(cls_id), f"classe_{cls_id}")
                    x1, y1, x2, y2 = map(int, box)
                    cor = CONFIG["CORES_PRODUTO"].get(classe, (180, 180, 180))
                    cor_rgb = (cor[2], cor[1], cor[0])

                    label = f"{classe}  {score:.1%}"
                    # Obter tamanho do texto via bbox
                    bbox = draw.textbbox((0, 0), label, font=font_medium)
                    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

                    draw.rectangle([x1, y1 - th - 12, x1 + tw + 10, y1], fill=cor_rgb)
                    draw.text((x1 + 5, y1 - th - 6), label, font=font_medium, fill=(255, 255, 255))

            # Status da balança (canto inferior)
            with lock_estado:
                lb = ultimas_leituras_balanca.get(id_sensor, {})
            peso_atual    = lb.get("peso",     0.0)
            variacao_atual = lb.get("variacao",  0.0)
            lb_ts          = lb.get("ts",        0)
            frescos = (agora - lb_ts) <= CONFIG["CORRELACAO_JANELA_S"]

            cor_status_rgb = (0, 220, 80) if frescos else (255, 60, 60)
            status_txt = "Ao vivo" if frescos else "Sem leitura"

            txt_hud_inf = f"Balança #{id_sensor}:  Peso={peso_atual:.1f}g   Variação={variacao_atual:+.1f}g   [{status_txt}]"
            draw.text((15, h - 45), txt_hud_inf, font=font_large, fill=cor_status_rgb)

            # Voltar para o OpenCV
            frame = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

            # Para iniciar em janela normal, a propriedade de tela cheia eh alternada na tecla F
            cv2.namedWindow("OunceAI Bridge", cv2.WINDOW_NORMAL)
            cv2.imshow("OunceAI Bridge", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                log.info("⛔ Encerrado pela tecla Q.")
                break
            elif key == ord("f"):
                # Alternar tela cheia
                prop = cv2.getWindowProperty("OunceAI Bridge", cv2.WND_PROP_FULLSCREEN)
                if prop == cv2.WINDOW_FULLSCREEN:
                    cv2.setWindowProperty("OunceAI Bridge", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                else:
                    cv2.setWindowProperty("OunceAI Bridge", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    cap.release()
    cv2.destroyAllWindows()


# ─────────────────────────────────────────────
# THREAD 3: Consumer → PostgreSQL
# ─────────────────────────────────────────────

def thread_postgres_writer():
    conn = conectar_pg()
    garantir_schema(conn)

    while True:
        try:
            evento = evento_queue.get(timeout=5)
        except queue.Empty:
            continue

        while True:
            try:
                gravar_evento(conn, evento)
                break
            except Exception as e:
                log.error(f"🔄 Reconectando PG após erro: {e}")
                try:
                    conn.close()
                except Exception:
                    pass
                conn = conectar_pg()
                garantir_schema(conn)


# ─────────────────────────────────────────────
# PONTO DE ENTRADA
# ─────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("  OunceAI Bridge — YOLO11 + HX711 → PostgreSQL")
    log.info("=" * 60)
    log.info(f"  Serial:     {CONFIG['SERIAL_PORT']} @ {CONFIG['BAUD_RATE']} baud")
    log.info(f"  Sensor ID:  {CONFIG['ID_SENSOR']}")
    log.info(f"  YOLO11:     {CONFIG['YOLO_MODEL']} (conf≥{CONFIG['YOLO_CONF']:.0%})")
    log.info(f"  Classes:    {list(CONFIG['CLASSES_MODELO'].values())}")
    log.info(f"  Câmera:     índice {CONFIG['CAMERA_INDEX']}")
    log.info(f"  PostgreSQL: {CONFIG['PG_HOST']}:{CONFIG['PG_PORT']}/{CONFIG['PG_DB']}")
    log.info("=" * 60)

    # Threads daemon
    threading.Thread(target=thread_serial,        daemon=True, name="Serial").start()
    threading.Thread(target=thread_postgres_writer, daemon=True, name="PGWriter").start()

    # Câmera roda na thread principal (OpenCV no Windows exige isso)
    thread_camera()


if __name__ == "__main__":
    main()
