import os
import json
import shutil
from core.paths import PREPROCESSAMENTO_DATA

CAMINHO_LIMPOS = PREPROCESSAMENTO_DATA / "Dados_Limpos_Iniciais"
CAMINHO_DESTINO = PREPROCESSAMENTO_DATA / "Dados_Prontos_Sem_Threshold"

def organizar_processaveis():
    if not os.path.exists(CAMINHO_DESTINO): os.makedirs(CAMINHO_DESTINO)
    arquivos = [f for f in os.listdir(CAMINHO_LIMPOS) if f.endswith('.json')]
    
    for arquivo in arquivos:
        with open(CAMINHO_LIMPOS / arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        if len(dados.get('posts', [])) > 0:
            shutil.copy2(CAMINHO_LIMPOS / arquivo, CAMINHO_DESTINO / arquivo)

if __name__ == "__main__":
    organizar_processaveis()