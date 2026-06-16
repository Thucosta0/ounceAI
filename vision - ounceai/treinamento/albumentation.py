#GERAR A IMAGEM
from google.colab import drive
drive.mount('/content/drive')

#!pip install albumentations opencv-python natsort
import albumentations as A
import cv2
import os
import natsort
from google.colab import drive

# 1. Garante que o natsort e albumentations estão instalados
#!pip install natsort albumentations -q

# 2. Configura as transformações MUITO MAIS BRUSCAS
transform = A.Compose([
    # Luz e Contraste extremos (simula câmera contra o sol ou no escuro)
    A.RandomBrightnessContrast(brightness_limit=0.4, contrast_limit=0.4, p=0.8),
    
    # Ruído muito mais visível (granulado forte)
    A.GaussNoise(var_limit=(50.0, 200.0), p=0.6),
    
    # Borrão de movimento forte (simula a câmera tremendo bastante)
    A.MotionBlur(blur_limit=15, p=0.5),
    
    # NOVO: Altera as cores da imagem (ajuda o modelo a não decorar as cores)
    A.HueSaturationValue(hue_shift_limit=20, sat_shift_limit=40, val_shift_limit=30, p=0.5),
    
    # NOVO: Gira até 30 graus, aproxima e arrasta a foto (o YOLO ajusta as boxes sozinho)
    A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.2, rotate_limit=30, p=0.5),
    
    # NOVO: Espelha a imagem horizontalmente (dobra a variedade do dataset grátis)
    A.HorizontalFlip(p=0.5),
    
], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))

# 3. Definição da Função
def augment_dataset(img_dir, label_dir, output_img_dir, output_label_dir, num_aug=2):
    if not os.path.exists(img_dir):
        print(f"❌ Erro: A pasta {img_dir} não foi encontrada!")
        return

    images = natsort.natsorted([f for f in os.listdir(img_dir) if f.endswith('.jpg')])

    for img_name in images:
        # Carrega Imagem
        image = cv2.imread(os.path.join(img_dir, img_name))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Carrega Labels (.txt)
        label_path = os.path.join(label_dir, img_name.replace('.jpg', '.txt'))

        if not os.path.exists(label_path):
            continue # Pula se não achar o arquivo de texto

        bboxes = []
        class_labels = []

        with open(label_path, 'r') as f:
            for line in f.readlines():
                vals = list(map(float, line.split()))
                class_labels.append(vals[0])
                bboxes.append(vals[1:])

        # Gera as variações
        for i in range(num_aug):
            try:
                augmented = transform(image=image, bboxes=bboxes, class_labels=class_labels)

                aug_img_name = f"aug_{i}_{img_name}"

                # Salva imagem
                cv2.imwrite(os.path.join(output_img_dir, aug_img_name),
                            cv2.cvtColor(augmented['image'], cv2.COLOR_RGB2BGR))

                # Salva label
                with open(os.path.join(output_label_dir, aug_img_name.replace('.jpg', '.txt')), 'w') as f:
                    for cl, box in zip(augmented['class_labels'], augmented['bboxes']):
                        f.write(f"{int(cl)} {' '.join(map(str, box))}\n")
            except Exception as e:
                print(f"Aviso: Falha ao aumentar {img_name}: {e}")

# --- EXECUÇÃO ---

img_entrada = '/content/drive/MyDrive/ounceia_datasetcp/train/images'
label_entrada = '/content/drive/MyDrive/ounceia_datasetcp/train/labels'

#savezada
img_saida = img_entrada
label_saida = label_entrada

augment_dataset(
    img_dir=img_entrada,
    label_dir=label_entrada,
    output_img_dir=img_saida,
    output_label_dir=label_saida,
    num_aug=2
)

print("🚀 Processo concluído! Suas fotos foram multiplicadas no Drive com distorções bruscas.")