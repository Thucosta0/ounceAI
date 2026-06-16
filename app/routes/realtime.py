from flask import Blueprint, jsonify
from app.core.database import _get_connection
from app.routes.auth import limiter
import psycopg2.extras

realtime_bp = Blueprint('realtime', __name__)

@realtime_bp.route('/events', methods=['GET'])
@limiter.exempt
def get_realtime_events():
    conn = _get_connection()
    if not conn:
        return jsonify({"error": "Erro de conexão com o banco"}), 500

    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Pega os últimos 5 eventos do banco de dados, ordenando pelo id_evento (mais recente primeiro)
        cur.execute("""
            SELECT 
                f.id_evento,
                f.fk_tempo,
                h.id_prateleira as equipamento,
                p.nome_produto as produto,
                f.status_auditoria as tipo,
                p.massa_nominal_gramas as massa_nominal
            FROM fato_auditoria_bimodal f
            JOIN dim_produto p ON f.fk_produto = p.sk_produto
            JOIN dim_hardware h ON f.fk_hardware = h.sk_hardware
            ORDER BY f.id_evento DESC
            LIMIT 5
        """)
        
        events = cur.fetchall()
        
        # Format the response
        result = []
        for evt in events:
            # fk_tempo é um inteiro no formato YYYYMMDDHH (ex: 2026061308 = 2026-06-13 08:00)
            fk_tempo_str = str(evt["fk_tempo"])
            horario_formatado = f"{fk_tempo_str[8:10]}:00:00"
            result.append({
            "id": evt["id_evento"],
            "horario": horario_formatado,
            "equipamento": evt["equipamento"],
            "produto": evt["produto"],
            "tipo": evt["tipo"],
            "massa_nominal": evt["massa_nominal"]
        })

        cur.close()
        conn.close()

        return jsonify({"success": True, "events": result}), 200
    except Exception as e:
        print(f"Erro em /api/realtime/events: {e}")
        return jsonify({"error": str(e)}), 500
