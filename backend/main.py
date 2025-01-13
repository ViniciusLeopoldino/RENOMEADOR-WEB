import os
import re
import zipfile
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_path
import pytesseract
import cv2
import numpy as np

# Configuração do Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\vinicius\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Configuração do FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diretórios
UPLOAD_DIRECTORY = "uploads"
RENAMED_DIRECTORY = "renamed"
ZIP_FILE_PATH = "renamed_files.zip"

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(RENAMED_DIRECTORY, exist_ok=True)

# Padrões de regex para identificar números de nota fiscal
PADROES_NF = [
    r"Nº\s*(\d{3}\.\d{3}\.\d{3})",  # "Nº xxx.xxx.xxx"
    r"No\.\s*(\d+)",                # "No. xxxxxxxxx"
    r"Nº\s*(\d+)",                  # "Nº xxxxxxxxx"
]

# Funções auxiliares
def melhorar_imagem(img):
    """Aplica processamento para melhorar a qualidade da imagem."""
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, img_bin = cv2.threshold(img_gray, 127, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    img_morph = cv2.morphologyEx(img_bin, cv2.MORPH_CLOSE, kernel)
    scale_percent = 200
    width = int(img_morph.shape[1] * scale_percent / 100)
    height = int(img_morph.shape[0] * scale_percent / 100)
    img_resized = cv2.resize(img_morph, (width, height), interpolation=cv2.INTER_CUBIC)
    return img_resized

def extrair_texto_pdf(caminho_pdf):
    """Extrai texto de um PDF usando OCR."""
    imagens = convert_from_path(caminho_pdf, poppler_path=r"C:\poppler\Library\bin")
    texto = ""
    for imagem in imagens:
        img_cv = np.array(imagem)
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
        img_processada = melhorar_imagem(img_cv)
        texto += pytesseract.image_to_string(img_processada, lang="por")
    return texto

def renomear_pdf(caminho_pdf, padroes, contador):
    """Renomeia um PDF com base nos padrões fornecidos."""
    texto = extrair_texto_pdf(caminho_pdf)
    for padrao in padroes:
        resultado = re.search(padrao, texto)
        if resultado:
            numero_nf = resultado.group(1)
            return f"{numero_nf}.pdf"
    return f"NF_{contador}.pdf"

# Endpoints
@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """Recebe e processa os arquivos enviados."""
    contador = 1
    for file in files:
        # Salva o arquivo original
        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Renomeia o arquivo
        novo_nome = renomear_pdf(file_path, PADROES_NF, contador)
        novo_caminho = os.path.join(RENAMED_DIRECTORY, novo_nome)
        os.rename(file_path, novo_caminho)
        contador += 1

    # Compacta os arquivos renomeados
    with zipfile.ZipFile(ZIP_FILE_PATH, "w") as zipf:
        for root, _, files in os.walk(RENAMED_DIRECTORY):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.basename(file_path))

    return {"message": "Arquivos processados com sucesso!", "download_url": "/download"}

@app.get("/download")
async def download_zip():
    """Permite o download do arquivo compactado."""
    if os.path.exists(ZIP_FILE_PATH):
        return FileResponse(ZIP_FILE_PATH, media_type="application/zip", filename="renamed_files.zip")
    return {"message": "Arquivo compactado não encontrado."}
