from gradio import Dataframe
import pandas as pd
import json

from core.paths import DATASET_FINAL_CSV, VALIDACAO_CONFIG

CAMINHO_ENTRADA_MODELOS = DATASET_FINAL_CSV / "dataset_laptops_GAMER_ONLY.csv"

CAMINHO_SAIDA_JSON = VALIDACAO_CONFIG / "dictionary_synonyms_refined.json"

def criar_dicionario_lowercase(df):
    # Definição de marcas e séries para busca de padrões
    marcas: list[str] = ['asus', 'acer', 'msi', 'dell', 'hp', 'lenovo', 'razer', 'gigabyte', 'alienware']

    series_fortes: set[str] = {
        'rog', 'tuf', 'zephyrus', 'strix', 'flow', 'scar', 'nitro', 'predator', 
        'helios', 'triton', 'victus', 'omen', 'legion', 'loq', 'stealth', 'raider',
        'katana', 'sword', 'pulse', 'vector', 'cyborg', 'crosshair', 'bravo'
    }
    
    # Palavras ignoradas quando sozinhas (evita sinônimos genéricos)
    stop_words: set[str] = {'gaming', 'laptop', 'notebook', 'oled', 'edition', 'advanced', 'thin', 'studio', 'pro'}
    
    modelos_unicos = df['modelo_limpo'].dropna().unique()
    print(type(modelos_unicos))
    
    dicionario: dict = {}

    for modelo_original in modelos_unicos:
        # Normaliza a chave principal para minúsculo
        nome_base:str = modelo_original.lower()
        sinonimos:set = set()
        partes:list[str] = nome_base.split()
        if not partes: continue
        
        marca = partes[0]
        
        for p in partes:
            termo:str = p.strip(',.()')
            
            # 1. Identificadores Técnicos (Alfanuméricos: letras + números)
            # Ex: an515, g533, 12uhs-226in
            if any(c.isdigit() for c in termo) and any(c.isalpha() for c in termo):
                # Remove sufixo regional 'in' se o código for longo
                if termo.endswith('in') and len(termo) > 5:
                    sinonimos.add(termo[:-2])
                sinonimos.add(termo)
                sinonimos.add(f"{marca} {termo}")
            
    #         # 2. Nomes de Séries (Ex: rog, nitro, helios)
            if termo in series_fortes:
                sinonimos.add(termo)
                sinonimos.add(f"{marca} {termo}")
            
    #         # 3. Tamanhos de Tela (13 a 18 polegadas)
            # Nunca isolados, sempre com a marca (Ex: asus 16)
            if termo.isdigit() and 13 <= int(termo) <= 18:
                sinonimos.add(f"{marca} {termo}")

    #     # Filtro final para garantir qualidade
        lista_final = []
        for s in sinonimos:
            if s == nome_base: continue
            if s in stop_words: continue
            if len(s) < 2: continue
            # Remove números puros menores que 100
            if s.isdigit() and int(s) < 100: continue
            lista_final.append(s)
            
        dicionario[nome_base] = sorted(list(set(lista_final)))

    return dicionario

# Execução e salvamento
df:Dataframe = pd.read_csv(CAMINHO_ENTRADA_MODELOS)
resultado_dict:dict = criar_dicionario_lowercase(df)

with open(CAMINHO_SAIDA_JSON, 'w', encoding='utf-8') as f:
    json.dump(resultado_dict, f, indent=4, ensure_ascii=False)