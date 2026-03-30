import os
import json
from pathlib import Path
from tqdm import tqdm
from core.paths import PREPROCESSAMENTO_DATA

# Entrada: A pasta com os 1.058 ficheiros fragmentados
CAMINHO_ENTRADA = PREPROCESSAMENTO_DATA / "Dados_Prontos_Sem_Threshold"
# Saída: Onde estarão os ~160 modelos únicos
CAMINHO_CONSOLIDADO = PREPROCESSAMENTO_DATA / "Dados_Consolidados_Por_Modelo"

def consolidar_data():
    if not CAMINHO_CONSOLIDADO.exists(): CAMINHO_CONSOLIDADO.mkdir(parents=True)
    
    arquivos = list(CAMINHO_ENTRADA.glob("*.json"))
    repositorio = {} # Chave: Nome do Modelo, Valor: Dados Consolidados

    print(f"📦 Consolidando {len(arquivos)} ficheiros em modelos únicos...")

    for arq in tqdm(arquivos):
        with open(arq, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            
        modelo_id = dados.get('modelo_busca_utilizado', 'Desconhecido').strip()
        posts = dados.get('posts', [])

        if modelo_id not in repositorio:
            repositorio[modelo_id] = {
                "modelo_busca_utilizado": modelo_id,
                "posts": [],
                "ids_vistos": set()
            }
        
        # Adiciona posts evitando duplicatas globais para este modelo
        for p in posts:
            p_id = p.get('id')
            if p_id not in repositorio[modelo_id]["ids_vistos"]:
                repositorio[modelo_id]["posts"].append(p)
                repositorio[modelo_id]["ids_vistos"].add(p_id)

    # Guardar os ficheiros consolidados
    for mod_nome, conteudo in repositorio.items():
        # Limpa o nome para o sistema de ficheiros
        nome_limpo = "".join([c if c.isalnum() else "_" for c in mod_nome])
        
        # Remove o set de IDs antes de guardar o JSON
        del conteudo["ids_vistos"]
        
        with open(CAMINHO_CONSOLIDADO / f"{nome_limpo}.json", 'w', encoding='utf-8') as f:
            json.dump(conteudo, f, indent=4, ensure_ascii=False)

    print(f"✅ Consolidação concluída: {len(repositorio)} modelos únicos gerados.")

if __name__ == "__main__":
    consolidar_data()