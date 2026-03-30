
import sys
from pathlib import Path
import csv
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import traceback 
import os
import tempfile
# --- IMPORTAÇÃO CRUCIAL PARA PARALELISMO ---
import multiprocessing as mp 

# [IMPORTAÇÕES NECESSÁRIAS PARA SELENIUM/UNDETECTED]
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

# Obtém o caminho absoluto da pasta do script atual.
caminho_script = Path(__file__).resolve().parent
caminho_raiz_projeto = caminho_script.parent.parent
sys.path.append(str(caminho_raiz_projeto))

from config import DIRETORIO_DADOS_WEBSCRAPPING,DIRETORIO_DADOS_EXTRACAO_QA

# --- SELETORES HTML (CONSTANTES) ---
SELETOR_TITULO = 'h1'
SELETOR_CONTEUDO_POST = 'conversation-balloon__content__text'
SELETOR_COMENTARIOS_LISTA = 'comment-list__comment'
SELETOR_CONTEUDO_COMENTARIO = 'dell-comment-balloon__content'
SELETOR_ESPERA_CONTEUDO = (By.CLASS_NAME, 'conversation-balloon__content__text') 

# --- CONFIGURAÇÃO DE ARQUIVOS E CHECKPOINT ---
ARQUIVO_PROGRESSO = DIRETORIO_DADOS_WEBSCRAPPING / 'progresso_dell_community_ingles.txt'
caminho_entrada = DIRETORIO_DADOS_WEBSCRAPPING /'links_discussoes_Dell_Ingles.csv'
caminho_saida_perguntas = DIRETORIO_DADOS_EXTRACAO_QA /'perguntas/posts_DellCommunity_Ingles_Perguntas_FINAL.csv'
caminho_saida_respostas = DIRETORIO_DADOS_EXTRACAO_QA /'respostas/comentarios_DellCommunity_Ingles_Respostas_FINAL.csv'
NOME_COLUNA_URL= 'Link da Discussão'

HEADERS = {
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.6647.0 Safari/537.36',
'Accept-Language': 'en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7',
'Accept-Encoding': 'gzip, deflate, br',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,application/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
}

# Para garantir que a escrita no arquivo de progresso seja segura
progress_lock = mp.Lock() 

# --- FUNÇÕES DE CHECKPOINT ---
def carregar_progresso():
    """Tenta carregar os links já processados do arquivo de progresso."""
    urls_processadas = set()
    if ARQUIVO_PROGRESSO.exists():
        with open(ARQUIVO_PROGRESSO, 'r', encoding='utf-8') as f:
            for line in f:
                urls_processadas.add(line.strip())
        print(f"Progresso encontrado. {len(urls_processadas)} links já foram processados.")
    return urls_processadas

def salvar_progresso(url):
    """Salva um URL no arquivo de progresso de forma segura."""
    with progress_lock:
        with open(ARQUIVO_PROGRESSO, 'a', encoding='utf-8') as f:
            f.write(url + '\n')

# --- SOLUÇÃO: CONFIGURAÇÃO ÚNICA DO CHROMEDRIVER ---
def configurar_driver_unico():
    """
    Configura o ChromeDriver uma única vez para evitar conflitos de concorrência.
    Retorna o caminho do executável configurado.
    """
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    
    # Cria um diretório temporário único para este processo
    temp_dir = tempfile.mkdtemp()
    
    try:
        driver = uc.Chrome(
            version_main=141, 
            options=chrome_options,
            user_data_dir=temp_dir
        )
        driver_path = driver.patcher.executable_path
        driver.quit()
        return driver_path
    except Exception as e:
        print(f"❌ Erro na configuração do driver: {e}")
        return None

# --- FUNÇÃO WORKER COM DRIVER PRÉ-CONFIGURADO ---
def worker_extrair_dados(url, post_id, driver_exec_path):
    """
    Função Worker que utiliza um driver já configurado.
    """
    driver = None
    post_data_list = []
    comments_list = []
    
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")

    try:
        # SOLUÇÃO: Usar o driver_path pré-configurado e user_data_dir único
        temp_dir = tempfile.mkdtemp()
        
        driver = uc.Chrome(
            driver_executable_path=driver_exec_path,
            options=chrome_options,
            user_data_dir=temp_dir
        ) 
        
        wait_selenium = WebDriverWait(driver, 10) 
        
        # --- Configuração Anti-Bloqueio ---
        pausa_nav = random.uniform(1, 2) 
        time.sleep(pausa_nav)
        
        # 1. Navegar para a URL
        driver.get(url)
        
        # 2. Esperar que o conteúdo principal esteja visível
        wait_selenium.until(EC.visibility_of_element_located(SELETOR_ESPERA_CONTEUDO))
        
        # 3. Extrair o HTML e processar com BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # --- Extração (Posts) ---
        titulo_elem = soup.find(SELETOR_TITULO)
        page_title = titulo_elem.string.strip() if titulo_elem and titulo_elem.string else "Título não encontrado"

        texto_postagem_elem = soup.find(class_=SELETOR_CONTEUDO_POST)
        post_content = texto_postagem_elem.text.strip() if texto_postagem_elem else "Conteúdo não encontrado"

        post_data = {
            "ID_Post": post_id,
            "Titulo_Post": page_title,
            "URL_Post": url,
            "Conteudo_Post": post_content.replace('\n', ' ').replace('\r', '').strip()
        }
        post_data_list.append(post_data)

        # --- Extração (Comentários) ---
        all_comments = soup.find_all(class_=SELETOR_COMENTARIOS_LISTA)
        for comment in all_comments:
            comment_content_elem = comment.find(class_=SELETOR_CONTEUDO_COMENTARIO)
            comment_content = comment_content_elem.text.strip() if comment_content_elem else "Comentário não encontrado"
            
            if comment_content and comment_content != "Comentário não encontrado":
                comments_list.append({
                    "ID_Post": post_id,
                    "Conteudo_Comentario": comment_content.replace('\n', ' ').replace('\r', '').strip()
                })
        
        # 4. Salva o progresso IMEDIATAMENTE
        salvar_progresso(url)
        
        return (url, True, post_data_list, comments_list)
        
    except (TimeoutException, WebDriverException, NoSuchElementException) as e:
        print(f"[{post_id}] ❌ Erro de Selenium (Timeout/Nav/Elemento): {url}. Erro: {e}")
        print(f"[{post_id}] Pausa extra de 10s para evitar bloqueio.")
        time.sleep(10)
        return (url, False, [], [])
        
    except Exception as e:
        print(f"[{post_id}] ❌ Erro Crítico não tratado: {url}. Erro: {e}")
        traceback.print_exc()
        return (url, False, [], [])
        
    finally:
        # Limpeza do diretório temporário
        try:
            if driver:
                driver.quit()
            # Remove o diretório temporário se existir
            if 'temp_dir' in locals():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"[{post_id}] ⚠️ Erro na limpeza: {e}")

# --- Código Principal Modificado ---
def main():
    start_time = time.time()
    
    links_para_processar = []
    urls_processadas_anteriormente = carregar_progresso()
    posts_data = []
    comments_data = []
    LINKS_IGNORADOS = 0
    
    # 1. CONFIGURAÇÃO ÚNICA DO DRIVER (antes do pool)
    print("🔄 Configurando ChromeDriver...")
    driver_exec_path = configurar_driver_unico()
    
    if not driver_exec_path:
        print("❌ Falha crítica na configuração do ChromeDriver. Abortando.")
        return
    
    print(f"✅ ChromeDriver configurado: {driver_exec_path}")
    
    # 2. Carrega e filtra todos os links do CSV
    try:
        with open(caminho_entrada, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            if NOME_COLUNA_URL not in reader.fieldnames:
                print(f"Erro: O arquivo CSV de entrada deve ter uma coluna chamada '{NOME_COLUNA_URL}'.")
                return
            
            for index, row in enumerate(reader):
                url = row[NOME_COLUNA_URL].strip()
                
                # Filtra links já processados (Checkpointing)
                if url in urls_processadas_anteriormente:
                    LINKS_IGNORADOS += 1
                    continue
                
                if url:
                    # Adiciona (URL, ID do Post, driver_path)
                    links_para_processar.append((url, index, driver_exec_path)) 
        
        TOTAL_LINKS_NA_SESSAO = len(links_para_processar)
        print(f"Links a processar nesta sessão: {TOTAL_LINKS_NA_SESSAO}. Links ignorados (já processados): {LINKS_IGNORADOS}.")

        if TOTAL_LINKS_NA_SESSAO == 0:
            print("Todos os links já foram processados. Saindo.")
            return

        # 3. Execução PARALELA usando mp.Pool
        NUM_PROCESSOS = min(4, TOTAL_LINKS_NA_SESSAO)
        LINKS_PROCESSADOS_NA_SESSAO = 0
        
        print(f"\n--- INICIANDO EXTRAÇÃO PARALELA com {NUM_PROCESSOS} processos ---")
        
        with mp.Pool(processes=NUM_PROCESSOS) as pool:
            
            # Envia a lista de argumentos para a função worker
            results_async = pool.starmap_async(worker_extrair_dados, links_para_processar)
            
            # Loop de monitoramento de progresso
            while not results_async.ready():
                time.sleep(5) 
                
                processados_agora = len(carregar_progresso()) - len(urls_processadas_anteriormente)
                
                if processados_agora > LINKS_PROCESSADOS_NA_SESSAO:
                    LINKS_PROCESSADOS_NA_SESSAO = processados_agora
                    
                    total_disponivel = TOTAL_LINKS_NA_SESSAO + LINKS_IGNORADOS
                    total_processado_atual = LINKS_PROCESSADOS_NA_SESSAO + len(urls_processadas_anteriormente)
                    
                    percentual_global = (total_processado_atual) * 100 / (total_disponivel)
                    
                    print(f"🤖 [Status Parcial] Processado nesta sessão: {LINKS_PROCESSADOS_NA_SESSAO}/{TOTAL_LINKS_NA_SESSAO}. Acumulado total: {total_processado_atual}. Percentual global: {percentual_global:.2f}%.")
                    print("----------------------------------------------------------------------")
            
            all_results = results_async.get()
        
        # 4. Consolidação dos Dados
        success_count = 0
        for url, success, post_data_list_worker, comments_list_worker in all_results:
            if success:
                success_count += 1
                posts_data.extend(post_data_list_worker)
                comments_data.extend(comments_list_worker)
                
        LINKS_PROCESSADOS_NA_SESSAO = success_count

    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_entrada}' não foi encontrado.")
        
    except Exception as e:
        print(f"Ocorreu um erro durante a execução principal: {e}")
        traceback.print_exc()

    # 5. Salvamento dos Dados Finais
    print("\n--- Salvamento dos Dados Finais em arquivos CSV ---")
    
    # Garante que os diretórios existam
    DIRETORIO_DADOS_EXTRACAO_QA.mkdir(parents=True, exist_ok=True)
    caminho_saida_perguntas.parent.mkdir(parents=True, exist_ok=True)
    caminho_saida_respostas.parent.mkdir(parents=True, exist_ok=True)
    
    if posts_data:
        df_posts = pd.DataFrame(posts_data)
        df_posts.to_csv(caminho_saida_perguntas, index=False, encoding='utf-8', mode='a', header=not caminho_saida_perguntas.exists())
        print(f"Dados de posts salvos em '{caminho_saida_perguntas}'. Total: {len(df_posts)} (Novos).")
    else:
        print("Nenhum dado de post foi extraído.")

    if comments_data:
        df_comments = pd.DataFrame(comments_data)
        df_comments.to_csv(caminho_saida_respostas, index=False, encoding='utf-8', mode='a', header=not caminho_saida_respostas.exists())
        print(f"Dados de comentários salvos em '{caminho_saida_respostas}'. Total: {len(df_comments)} (Novos).")
    else:
        print("Nenhum dado de comentário foi extraído.")

    end_time = time.time()
    total_duration = end_time - start_time
    taxa = LINKS_PROCESSADOS_NA_SESSAO / total_duration if total_duration > 0 and LINKS_PROCESSADOS_NA_SESSAO > 0 else 0 
    
    print(f"\nProcesso concluído! Duração total da sessão: {total_duration:.2f} segundos.")
    print(f"Links processados com sucesso nesta sessão: {LINKS_PROCESSADOS_NA_SESSAO}")
    print(f"Taxa total da sessão: {taxa:.2f} links/segundo.")

if __name__ == "__main__":
    main()