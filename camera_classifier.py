"""
============================================================
 OunceAI — Câmera YOLO11: Classifica Objeto + Envia ao Banco
============================================================
 Modelo customizado: model_yolo11_0.1.pt
 Classes treinadas (nc=3):
   0 → Caixa de Leite
   1 → Coca Cola
   2 → Guarana

 Captura frames, roda inferência YOLO11, exibe qual balança
 detectou o produto (confiança + classe) e salva o evento na
 tabela fato_auditoria_bimodal do PostgreSQL.

 Dependências:
   pip install ultralytics opencv-python psycopg2-binary
               python-dotenv numpy
============================================================
"""

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
from dotenv import load_dotenv

# YOLO (Ultralytics)
try:
    from ultralytics import YOLO
except ImportError:
    print("❌ Instale o ultralytics: pip install ultralytics")
    sys.exit(1)

load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────
CONFIG = {
    # Câmera
    "CAMERA_INDEX":     int(os.getenv("CAMERA_INDEX", "0")),   # 0 = câmera padrão
    "FRAME_WIDTH":      int(os.getenv("FRAME_WIDTH",  "1280")),
    "FRAME_HEIGHT":     int(os.getenv("FRAME_HEIGHT", "720")),
    "FPS_TARGET":       int(os.getenv("FPS_TARGET",   "15")),

    # YOLO — modelo customizado OunceAI
    "YOLO_MODEL_PATH":  os.getenv("YOLO_MODEL_PATH", "model_yolo11_0.1.pt"),
    "YOLO_CONFIDENCE":  float(os.getenv("YOLO_CONFIDENCE", "0.50")),  # 50% mín para modelo treinado
    "YOLO_IOU":         float(os.getenv("YOLO_IOU",        "0.45")),

    # Classes do modelo treinado (nc=3) — NÃO ALTERE A ORDEM
    # Devem bater exatamente com nome_produto na dim_produto
    "CLASSES_MODELO": {
        0: "Leite Italac 1L",
        1: "Coca Cola Lata 350",
        2: "Guarana Lata 350",
    },

    # Mapeamento câmera → balança (id_sensor_hx711)
    # Edite conforme a instalação física das câmeras
    "CAMERA_SENSOR_MAP": {
        0: 1,   # câmera 0 → balança com id_sensor_hx711 = 1
        1: 2,   # câmera 1 → balança 2
    },

    # PostgreSQL
    "PG_HOST":  os.getenv("PG_HOST",  "localhost"),
    "PG_PORT":  int(os.getenv("PG_PORT", "5432")),
    "PG_DB":    os.getenv("PG_DB",    "ounceai_db"),
    "PG_USER":  os.getenv("PG_USER",  "ounceAI"),
    "PG_PASS":  os.getenv("PG_PASS",  "OnçaPintuda"),

    # Comportamento
    "MIN_INTERVALO_DETECCAO_S": 2.0,   # só grava nova detecção após N segundos
    "MOSTRAR_JANELA":           True,   # False para modo headless (servidor sem display)
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
        logging.FileHandler("camera.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("ounce.camera")

# ─────────────────────────────────────────────
# FILA DE DETECÇÕES
# ─────────────────────────────────────────────
deteccao_queue: queue.Queue = queue.Queue(maxsize=200)


# ─────────────────────────────────────────────
# BANCO DE DADOS
# ─────────────────────────────────────────────

def conectar_pg() -> psycopg2.extensions.connection:
    while True:
        try:
            conn = psycopg2.connect(
                host=CONFIG["PG_HOST"],
                port=CONFIG["PG_PORT"],
                dbname=CONFIG["PG_DB"],
                user=CONFIG["PG_USER"],
                password=CONFIG["PG_PASS"],
                connect_timeout=10,
            )
            conn.autocommit = False
            log.info(f"✅ PostgreSQL conectado.")
            return conn
        except psycopg2.OperationalError as e:
            log.error(f"❌ Falha PG: {e}")
            time.sleep(CONFIG["RECONNECT_DELAY_S"])


def obter_fk_produto(conn, nome_classe: str) -> int | None:
    """
    Busca o sk_produto da dim_produto pelo nome_produto (ILIKE).
    Retorna None se não encontrar.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT sk_produto FROM dim_produto WHERE LOWER(nome_produto) = LOWER(%s) LIMIT 1",
            (nome_classe,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def obter_fk_hardware(conn, id_sensor: int) -> int | None:
    """Busca o sk_hardware pelo id_sensor_hx711."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT sk_hardware FROM dim_hardware WHERE id_sensor_hx711 = %s LIMIT 1",
            (id_sensor,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def gerar_sk_tempo(conn, ts: datetime) -> int:
    """
    Insere (ou busca) a chave de tempo na dim_tempo.
    Chave = YYYYMMDDHH (ex: 2026060816)
    """
    sk = int(ts.strftime("%Y%m%d%H"))
    with conn.cursor() as cur:
        cur.execute("SELECT sk_tempo FROM dim_tempo WHERE sk_tempo = %s", (sk,))
        if not cur.fetchone():
            dia_semana = ["Segunda", "Terça", "Quarta", "Quinta",
                          "Sexta", "Sábado", "Domingo"][ts.weekday()]
            hora = ts.hour
            if 6 <= hora < 12:
                turno = "Manhã"
            elif 12 <= hora < 18:
                turno = "Tarde"
            elif 18 <= hora < 22:
                turno = "Noite"
            else:
                turno = "Madrugada"

            cur.execute("""
                INSERT INTO dim_tempo
                    (sk_tempo, data_completa, ano, mes, dia, hora, minuto, dia_semana, turno)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (sk_tempo) DO NOTHING
            """, (sk, ts, ts.year, ts.month, ts.day, ts.hour, ts.minute, dia_semana, turno))
    return sk


def gravar_deteccao(conn, deteccao: dict):
    """Insere um evento de detecção na fato_auditoria_bimodal."""
    ts    = deteccao["timestamp"]
    nome  = deteccao["classe"]
    conf  = deteccao["confianca"]
    delta = deteccao.get("delta_massa", 0.0)
    id_sensor = deteccao["id_sensor"]

    try:
        fk_produto  = obter_fk_produto(conn, nome)
        fk_hardware = obter_fk_hardware(conn, id_sensor)

        if fk_produto is None:
            log.warning(f"⚠️  Produto '{nome}' não encontrado na dim_produto — inserção ignorada.")
            return
        if fk_hardware is None:
            log.warning(f"⚠️  Sensor {id_sensor} não encontrado na dim_hardware — inserção ignorada.")
            return

        fk_tempo = gerar_sk_tempo(conn, ts)

        # Regra de auditoria simples (o ETL Orange refina depois)
        if conf >= 0.8 and abs(delta) > 5:
            status    = "Validado"
            receita   = deteccao.get("preco_unitario", 0.0)
            perda_est = 0.0
        elif conf < 0.5:
            status    = "Divergência Fantasma"
            receita   = 0.0
            perda_est = 0.0
        elif abs(delta) <= 5:
            status    = "Reposição"
            receita   = 0.0
            perda_est = 0.0
        else:
            status    = "Suspeito"
            receita   = 0.0
            perda_est = deteccao.get("preco_unitario", 0.0)

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO fato_auditoria_bimodal
                    (fk_produto, fk_hardware, fk_tempo,
                     delta_massa_gramas, dwell_time_segundos,
                     yolo_confidence_score, ia_detectou,
                     status_auditoria, receita_protegida, perda_estimada)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                fk_produto, fk_hardware, fk_tempo,
                round(delta, 2), int(deteccao.get("dwell_time", 1)),
                round(conf, 4), True,
                status, round(receita, 2), round(perda_est, 2),
            ))
        conn.commit()
        log.info(
            f"💾 Evento gravado | Produto: {nome} | Confiança: {conf:.1%} "
            f"| Delta: {delta:.1f}g | Status: {status} | Balança: {id_sensor}"
        )

    except psycopg2.Error as e:
        conn.rollback()
        log.error(f"❌ Erro ao gravar detecção: {e}")
        raise


# ─────────────────────────────────────────────
# OVERLAY VISUAL
# ─────────────────────────────────────────────

# Paleta de cores fixa por classe (BGR) — modelo OunceAI nc=3
COR_CLASSES: dict[str, tuple] = {
    "Leite Italac 1L":    (30,  200, 255),   # Amarelo/Ouro
    "Coca Cola Lata 350": (0,   30,  210),   # Vermelho
    "Guarana Lata 350":   (30,  180,  60),   # Verde
}

def cor_para_classe(classe: str) -> tuple:
    if classe not in COR_CLASSES:
        # fallback para classes inesperadas
        rng = np.random.default_rng(abs(hash(classe)) % (2**32))
        r, g, b = rng.integers(80, 230, size=3).tolist()
        COR_CLASSES[classe] = (b, g, r)
    return COR_CLASSES[classe]


def desenhar_overlay(
    frame: np.ndarray,
    results,
    id_sensor: int,
    fps: float,
) -> np.ndarray:
    """Desenha bounding boxes, labels e HUD no frame."""
    h, w = frame.shape[:2]

    # HUD — cabeçalho
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 60), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    cv2.putText(frame,
        f"OunceAI  |  Balanca #{id_sensor}  |  {fps:.1f} FPS  |  {datetime.now().strftime('%H:%M:%S')}",
        (12, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    if results and results[0].boxes is not None:
        boxes    = results[0].boxes.xyxy.cpu().numpy()
        scores   = results[0].boxes.conf.cpu().numpy()
        class_ids = results[0].boxes.cls.cpu().numpy().astype(int)
        names    = results[0].names

        for box, score, cls_id in zip(boxes, scores, class_ids):
            if score < CONFIG["YOLO_CONFIDENCE"]:
                continue

            x1, y1, x2, y2 = map(int, box)
            classe = names[cls_id]
            cor    = cor_para_classe(classe)

            # Bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), cor, 2)

            # Label background
            label = f"{classe}  {score:.1%}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 8, y1), cor, -1)
            cv2.putText(frame, label, (x1 + 4, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return frame


# ─────────────────────────────────────────────
# THREAD PRODUCER: câmera + YOLO
# ─────────────────────────────────────────────

def producer_camera():
    """
    Captura frames, roda YOLO e enfileira detecções.
    """
    log.info(f"📷 Carregando modelo YOLO11: {CONFIG['YOLO_MODEL_PATH']}")
    model = YOLO(CONFIG["YOLO_MODEL_PATH"])
    # Sobrescreve nomes do modelo com os nomes PT-BR configurados
    model.model.names = CONFIG["CLASSES_MODELO"]
    log.info(f"✅ Modelo YOLO11 carregado. Classes: {CONFIG['CLASSES_MODELO']}")

    id_sensor = CONFIG["CAMERA_SENSOR_MAP"].get(CONFIG["CAMERA_INDEX"], 1)

    cap = cv2.VideoCapture(CONFIG["CAMERA_INDEX"])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CONFIG["FRAME_WIDTH"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG["FRAME_HEIGHT"])
    cap.set(cv2.CAP_PROP_FPS, CONFIG["FPS_TARGET"])

    if not cap.isOpened():
        log.error(f"❌ Não foi possível abrir câmera índice {CONFIG['CAMERA_INDEX']}")
        sys.exit(1)

    log.info(f"✅ Câmera {CONFIG['CAMERA_INDEX']} aberta (sensor={id_sensor})")

    ultima_deteccao_ts: dict[str, float] = {}
    fps_counter = 0
    fps_ts = time.time()
    fps = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            log.warning("⚠️  Frame vazio — reconectando câmera...")
            cap.release()
            time.sleep(1)
            cap = cv2.VideoCapture(CONFIG["CAMERA_INDEX"])
            continue

        # Inferência YOLO
        results = model.predict(
            source=frame,
            conf=CONFIG["YOLO_CONFIDENCE"],
            iou=CONFIG["YOLO_IOU"],
            verbose=False,
            stream=False,
        )

        ts_agora = time.time()
        fps_counter += 1
        if ts_agora - fps_ts >= 1.0:
            fps = fps_counter / (ts_agora - fps_ts)
            fps_counter = 0
            fps_ts = ts_agora

        # Processar cada detecção
        if results and results[0].boxes is not None:
            boxes     = results[0].boxes.xyxy.cpu().numpy()
            scores    = results[0].boxes.conf.cpu().numpy()
            class_ids = results[0].boxes.cls.cpu().numpy().astype(int)
            names     = results[0].names

            for box, score, cls_id in zip(boxes, scores, class_ids):
                # Usa mapeamento garantido das classes do modelo customizado
                classe = CONFIG["CLASSES_MODELO"].get(int(cls_id), names.get(cls_id, f"classe_{cls_id}"))
                agora  = ts_agora
                ultimo = ultima_deteccao_ts.get(classe, 0)

                if agora - ultimo < CONFIG["MIN_INTERVALO_DETECCAO_S"]:
                    continue  # evita spam de eventos duplicados

                ultima_deteccao_ts[classe] = agora

                deteccao = {
                    "timestamp":  datetime.now(),
                    "classe":     classe,
                    "classe_id":  int(cls_id),
                    "confianca":  float(score),
                    "bbox":       box.tolist(),
                    "id_sensor":  id_sensor,
                    "delta_massa":  0.0,   # ← preenchido pelo bridge se integrado
                    "dwell_time": 1,
                }

                try:
                    deteccao_queue.put_nowait(deteccao)
                    log.info(
                        f"🔍 [{int(cls_id)}] {classe} | Conf: {score:.1%} "
                        f"| Balança: #{id_sensor}"
                    )
                except queue.Full:
                    log.warning("⚠️  Fila de detecções cheia!")

        # Exibição visual
        if CONFIG["MOSTRAR_JANELA"]:
            frame_display = desenhar_overlay(frame, results, id_sensor, fps)
            cv2.imshow("OunceAI — Câmera YOLO", frame_display)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                log.info("⛔ Encerrado pela tecla Q.")
                break

    cap.release()
    cv2.destroyAllWindows()


# ─────────────────────────────────────────────
# THREAD CONSUMER: detecções → PostgreSQL
# ─────────────────────────────────────────────

def consumer_postgres():
    conn = conectar_pg()

    while True:
        try:
            deteccao = deteccao_queue.get(timeout=5)
        except queue.Empty:
            continue

        while True:
            try:
                gravar_deteccao(conn, deteccao)
                break
            except Exception:
                log.error("🔄 Reconectando PostgreSQL...")
                try:
                    conn.close()
                except Exception:
                    pass
                conn = conectar_pg()


# ─────────────────────────────────────────────
# PONTO DE ENTRADA
# ─────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("  OunceAI — Câmera YOLO11 → PostgreSQL")
    log.info("=" * 60)
    log.info(f"  Modelo:   {CONFIG['YOLO_MODEL_PATH']}")
    log.info(f"  Classes:  {list(CONFIG['CLASSES_MODELO'].values())}")
    log.info(f"  Câmera:   índice {CONFIG['CAMERA_INDEX']}")
    log.info(f"  Confiança mínima: {CONFIG['YOLO_CONFIDENCE']:.0%}")

    t_pg = threading.Thread(target=consumer_postgres, daemon=True, name="CameraPGWriter")
    t_pg.start()

    # Producer roda na thread principal (necessário para cv2 no Windows)
    producer_camera()


if __name__ == "__main__":
    main()
