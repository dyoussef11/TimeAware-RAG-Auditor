import pandas as pd
import re
from pathlib import Path
from core.paths import DATASET_GAMER

def limpar_sku(texto):
    if pd.isna(texto): return ""
    texto = str(texto).lower()
    # Captura variações: i7, Ryzen 5, M4, Ultra 7
    intel = re.search(r'\b(i[3579]|ultra [3579]|core [3579])\b', texto)
    ryzen = re.search(r'\b(ryzen [3579])\b', texto)
    apple = re.search(r'\b(m[1234][\s]?(pro|max|ultra)?)\b', texto)
    
    if intel: return intel.group(1).upper().replace("CORE ", "I").replace("ULTRA ", "U")
    if ryzen: return ryzen.group(1).upper()
    if apple: return apple.group(1).upper()
    return ""

def extrair_modelo_puro(texto, marca):
    if pd.isna(texto): return ""
    texto = str(texto).lower()
    marca = str(marca).lower()
    
    # Limpeza de termos técnicos para isolar o nome comercial
    ruido = [marca, 'laptop', 'gaming', 'notebook', 'pc', '2023', '2024', 'inch', 'fhd', 'ips', 'dragon edition']
    for termo in ruido:
        texto = texto.replace(termo, '')
    
    # Pega o primeiro identificador alfanumérico (G15, V15, Legion, Victus, etc)
    match = re.search(r'\b([a-z]{1,2}\d{2,4}|[a-z]{3,15})\b', texto)
    return match.group(1).upper() if match else ""

def processar_arquivo(caminho_arq):
    # Força leitura inicial
    df = pd.read_csv(caminho_arq)
    # GARANTIA: Todas as colunas em minúsculo antes de qualquer lógica
    df.columns = [c.lower().strip() for c in df.columns]
    
    nome_arq = caminho_arq.name.lower()
    
    # MAPEAMENTO ROBUSTO (Chaves em minúsculo)
    # Usamos termos que existem nos nomes dos arquivos para identificar o mapa
    if "brand laptops" in nome_arq:
        m = {'marca': 'brand', 'modelo': 'model', 'cpu': 'processor_tier'}
    elif "brand-wise" in nome_arq:
        m = {'marca': 'company', 'modelo': 'product', 'cpu': 'cpu_model'}
    elif "flipkart" in nome_arq:
        m = {'marca': None, 'modelo': 'laptop_name', 'cpu': 'laptop_name'}
    elif "feature scaling" in nome_arq:
        m = {'marca': 'company', 'modelo': 'product', 'cpu': 'cpu'}
    elif "specifications dataset" in nome_arq and "prices" in nome_arq:
        m = {'marca': 'brand:', 'modelo': 'product_name', 'cpu': 'processor'}
    elif "cleaned" in nome_arq:
        m = {'marca': 'brand', 'modelo': 'model', 'cpu': 'cpu_series'}
    elif "predicting" in nome_arq:
        m = {'marca': 'brand', 'modelo': 'model_name', 'cpu': 'processor_name'}
    elif "specificaitons" in nome_arq: # Mantendo o erro de digitação do seu arquivo
        m = {'marca': 'brand', 'modelo': 'model_name', 'cpu': 'cpu'}
    elif "modern laptop" in nome_arq:
        m = {'marca': 'brand', 'modelo': 'model', 'cpu': 'cpu'}
    elif "unveiling" in nome_arq:
        m = {'marca': None, 'modelo': 'product', 'cpu': 'processor'}
    elif "gerado_ai" in nome_arq:
        m = {'marca': 'marca', 'modelo': 'modelo', 'cpu': 'modelo'}
    else:
        # Fallback genérico inteligente
        m = {
            'marca': next((c for c in df.columns if c in ['brand', 'brand:', 'company', 'marca']), None),
            'modelo': next((c for c in df.columns if c in ['model', 'model_name', 'product', 'product_name', 'modelo', 'laptop_name']), None),
            'cpu': next((c for c in df.columns if c in ['cpu', 'processor', 'cpu_model', 'processor_tier', 'processor_name']), None)
        }

    marca_col, modelo_col, cpu_col = m['marca'], m['modelo'], m['cpu']

    def construir_canonico(row):
        # 1. MARCA
        brand = ""
        if marca_col and marca_col in row.index:
            brand = str(row[marca_col]).strip().capitalize()
        
        # Se falhar ou for genérico, tenta extrair do texto do modelo
        if brand in ["", "Nan", "None", "Outros"] and modelo_col in row.index:
            for m_test in ['Dell', 'Hp', 'Acer', 'Lenovo', 'Asus', 'Msi', 'Apple', 'Samsung', 'Infinix', 'Tecno']:
                if m_test.lower() in str(row[modelo_col]).lower():
                    brand = m_test.capitalize()
                    break
        
        # 2. SKU (CPU)
        sku = ""
        if cpu_col and cpu_col in row.index:
            sku = limpar_sku(row[cpu_col])
        
        # 3. MODELO COMERCIAL
        model = ""
        if modelo_col and modelo_col in row.index:
            model = extrair_modelo_puro(row[modelo_col], brand)
        
        # Nome final: Marca + Modelo + SKU
        return " ".join(filter(None, [brand, model, sku])).strip()

    df['nome_canonico'] = df.apply(construir_canonico, axis=1)
    return df

# --- EXECUÇÃO ---
entrada = DATASET_GAMER / "dataset_limpos"
saida = DATASET_GAMER / "dataset_padronizados_V2"
saida.mkdir(parents=True, exist_ok=True)

for arq in entrada.glob("*.csv"):
    print(f"💎 Canonizando: {arq.name}")
    try:
        df_result = processar_arquivo(arq)
        df_result.to_csv(saida / f"CANON_{arq.name}", index=False)
    except Exception as e:
        print(f"❌ Erro em {arq.name}: {e}")

print(f"\n✨ Fim do processamento. Verifique: {saida}")