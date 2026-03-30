import os
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from core.paths import NER_DATA, NER

# --- CONFIGURAÇÕES (Devem ser as mesmas do seu script principal) ---
CAMINHO_ENTRADA =   NER_DATA / "reddit_50_notebooks_w_componentsV2.json"

DIR_CHECKPOINTS = NER_DATA / "checkpoints_ia_Llama"

def contar_total_posts(caminho_json):
    """
    Abre o arquivo de entrada uma única vez para contar quantos posts 
    totais precisam ser processados.
    """
    try:
        with open(caminho_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Se for uma lista de modelos, soma o tamanho da lista de posts de cada um
        if isinstance(dados, list):
            return sum(len(item.get('posts', [])) for item in dados)
        return len(dados.get('posts', []))
    except Exception as e:
        print(f"❌ Erro ao ler arquivo de entrada: {e}")
        return 0

def monitorar():
    """
    Monitora a pasta de checkpoints em tempo real, calculando a velocidade
    média e a estimativa de término (ETA).
    """
    print("📊 Iniciando Monitor de TCC...")
    total_posts = contar_total_posts(CAMINHO_ENTRADA)
    
    if total_posts == 0:
        print("⚠️ Não foi possível determinar o total de posts. Verifique o caminho do JSON.")
        return

    print(f"✅ Total de posts a processar: {total_posts}")
    print("-" * 50)

    # Variáveis para cálculo de velocidade
    start_time = time.time()
    # Pega a contagem inicial para calcular a velocidade a partir de agora
    checkpoints_iniciais = len(list(DIR_CHECKPOINTS.glob("*.json")))

    try:
        while True:
            # Lista arquivos atuais
            checkpoints_atuais = len(list(DIR_CHECKPOINTS.glob("*.json")))
            processados_agora = checkpoints_atuais - checkpoints_iniciais
            
            progresso = (checkpoints_atuais / total_posts) * 100
            elapsed = time.time() - start_time
            
            # Evita divisão por zero no início
            if processados_agora > 0:
                segundos_por_post = elapsed / processados_agora
                restantes = total_posts - checkpoints_atuais
                eta_segundos = restantes * segundos_por_post
                eta_data = datetime.now() + timedelta(seconds=eta_segundos)
                
                v_it_min = 60 / segundos_por_post
                
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"🚀 Status do TCC: {progresso:.2f}% concluído")
                print(f"📈 Progresso: {checkpoints_atuais} / {total_posts}")
                print(f"⚡ Velocidade Média: {segundos_por_post:.2f}s por post ({v_it_min:.2f} posts/min)")
                print(f"⏳ Tempo Restante: {str(timedelta(seconds=int(eta_segundos)))}")
                print(f"📅 Previsão de Término: {eta_data.strftime('%H:%M:%S (%d/%m)')}")
            else:
                print(f"⏱️ Aguardando conclusão do primeiro post para calcular ETA... ({checkpoints_atuais} já prontos)", end="\r")

            time.sleep(10) # Atualiza a cada 10 segundos para não pesar o IO
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoramento encerrado.")

if __name__ == "__main__":
    monitorar()