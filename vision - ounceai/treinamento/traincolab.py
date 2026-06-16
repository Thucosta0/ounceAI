
from ultralytics import YOLO

# 1. Carrega o modelo YOLOv8 nano
model = YOLO('yolov8n.pt')

# 2. Inicia o treinamento
# O arquivo data.yaml já está na raiz da sua pasta ounceia_dataset
model.train(
    data='/content/drive/MyDrive/ounceia_datasetcp/data.yaml',
    epochs=20,
    imgsz=640,       # Tamanho padrão de imagem
    batch=16,        # Quantidade de fotos processadas por vez
    project='/content/drive/MyDrive/ounceia_datasetcp/treinos',
    name='ia_v1_gratis',
    device=0         # Força o uso da GPU do Colab
)

print("✅ Treino finalizado! O arquivo 'best.pt' está na pasta de treinos.")