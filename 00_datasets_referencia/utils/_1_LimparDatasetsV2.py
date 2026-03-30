import pandas as pd
import numpy as np
from pathlib import Path
import sys
from core.paths import DATASET_GAMER

def limpar_dataset(df):
    """
    Aplica uma sequência de limpezas padronizadas no DataFrame
    """
    # 1. Normalizar nomes das colunas (Minúsculo, sem espaços, sem pontos)
    df.columns = (df.columns
                  .str.strip()
                  .str.lower()
                  .str.replace(' ', '_')
                  .str.replace('.', '', regex=False))

    # 2. Limpeza de Strings em todas as colunas de texto (object)
    for col in df.select_dtypes(include=['object']):
        # Converter para minúsculo e remover espaços nas extremidades
        df[col] = df[col].astype(str).str.lower().str.strip()
        
        # Opcional: Remover caracteres especiais básicos (ex: acentos simples)
        # Se quiser algo pesado, use a lib 'cleantext'
        df[col] = df[col].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

    # 3. Tratar valores ausentes (NaN)
    # Substitui strings vazias ou 'nan' por NaN real do numpy
    df = df.replace(['nan', 'none', ''], np.nan)
    
    # 4. Remover duplicatas
    duplicatas = df.duplicated().sum()
    if duplicatas > 0:
        print(f"   🧹 Removendo {duplicatas} linhas duplicadas...")
        df = df.drop_duplicates()

    return df

# --- Script Principal ---

caminho_filtrados = DATASET_GAMER / "dataset_filtrados_colunas"
caminho_limpos = DATASET_GAMER / "dataset_limposV2"
caminho_limpos.mkdir(parents=True, exist_ok=True)

# Listar arquivos disponíveis
arquivos = sorted(list(caminho_filtrados.glob("*.csv")))

if not arquivos:
    print(f"❌ Nenhum arquivo encontrado em {caminho_filtrados}")
    sys.exit()

print("\n--- SELECIONE O DATASET PARA LIMPEZA ---")
for i, arq in enumerate(arquivos):
    print(f"[{i}] {arq.name}")

escolha = input("\nDigite o número do arquivo (ou 'todos'): ")

try:
    if escolha.lower() == 'todos':
        selecionados = arquivos
    else:
        selecionados = [arquivos[int(escolha)]]

    for arq in selecionados:
        print(f"\n✨ Limpando: {arq.name}...")
        
        # Carregar (com fallback de encoding)
        try:
            df = pd.read_csv(arq)
        except:
            df = pd.read_csv(arq, encoding='latin1')

        # Aplicar limpeza
        df_limpo = limpar_dataset(df)

        # Salvar
        df_limpo.to_csv(caminho_limpos / arq.name, index=False)
        print(f"✅ Arquivo pronto em: {caminho_limpos / arq.name}")

except Exception as e:
    print(f"❌ Erro: {e}")