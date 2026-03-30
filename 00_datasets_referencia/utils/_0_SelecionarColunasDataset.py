import pandas as pd
from pathlib import Path
import sys
from core.paths import DATASET_KAGGLE, DATASET_GAMER 

# 1. Configurar caminhos
caminho_entrada = DATASET_KAGGLE
caminho_saida = DATASET_GAMER / "dataset_filtrados_colunas"
caminho_saida.mkdir(parents=True, exist_ok=True)

# 2. Listar todos os arquivos CSV
arquivos_csv = sorted(list(caminho_entrada.glob("*.csv")))

if not arquivos_csv:
    print(f"❌ Nenhum arquivo CSV encontrado em: {caminho_entrada}")
    sys.exit()

print(f"\n📂 Foram encontrados {len(arquivos_csv)} arquivos.")
print("Você definirá as colunas para CADA um deles agora.\n")

# 3. Loop Interativo Arquivo por Arquivo
for i, caminho_arq in enumerate(arquivos_csv, 1):
    nome_saida = caminho_saida / caminho_arq.name
    
    # Checkpoint: Pula se já existir
    if nome_saida.exists():
        print(f"⏩ [{i}/{len(arquivos_csv)}] Pulando: {caminho_arq.name} (Já existe)")
        continue

    print(f"\n" + "="*70)
    print(f"ARQUIVO ({i}/{len(arquivos_csv)}): {caminho_arq.name}")
    print("="*70)

    try:
        # Tenta ler com utf-8, se falhar usa latin1 (resolve o erro que você teve)
        try:
            df_temp = pd.read_csv(caminho_arq, nrows=1)
        except UnicodeDecodeError:
            df_temp = pd.read_csv(caminho_arq, nrows=1, encoding='latin1')
        
        colunas = df_temp.columns.tolist()

        # Exibe colunas de forma amigável
        for idx in range(0, len(colunas), 2):
            c1 = f"[{idx:2}] {colunas[idx]}"
            c2 = f"[{idx+1:2}] {colunas[idx+1]}" if idx+1 < len(colunas) else ""
            print(f"{c1:<35} {c2}")

        print("-" * 70)
        print("Digite os números das colunas separadas por vírgula.")
        print("Comandos: [p] Pular este arquivo | [s] Sair do script")
        entrada = input(f"Seleção para {caminho_arq.name}: ").strip().lower()

        if entrada == 's':
            print("\nEncerrando...")
            break
        if entrada == 'p' or entrada == '':
            print(f"Arquivo {caminho_arq.name} ignorado.")
            continue

        # Processa a escolha
        indices = [int(x.strip()) for x in entrada.split(',')]
        colunas_escolhidas = [colunas[idx] for idx in indices]

        # Lê o arquivo completo e filtra
        try:
            df_full = pd.read_csv(caminho_arq)
        except UnicodeDecodeError:
            df_full = pd.read_csv(caminho_arq, encoding='latin1')

        df_filtrado = df_full[colunas_escolhidas].copy()
        df_filtrado.to_csv(nome_saida, index=False)
        
        print(f"✅ Salvo com sucesso em: {nome_saida.name}")

    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupção detectada! Saindo...")
        sys.exit()
    except Exception as e:
        print(f"❌ Erro ao processar {caminho_arq.name}: {e}")
        continue

print(f"\n✨ Processamento finalizado! Verifique em: {caminho_saida}")