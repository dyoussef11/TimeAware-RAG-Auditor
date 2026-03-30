
import sys
from pathlib import Path
import csv
import pandas as pd
from bs4 import BeautifulSoup
import time
from threading import Lock 
import random
import traceback 
import os
import tempfile
# --- IMPORTAÇÃO CRUCIAL PARA PARALELISMO ---
import multiprocessing as mp 
# --- NOVA IMPORTAÇÃO TQDM ---
from tqdm import tqdm

# [IMPORTAÇÕES NECESSÁRIAS PARA SELENIUM/UNDETECTED]
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

# Obtém o caminho absoluto da pasta do script atual.
caminho_script = Path(__file__).resolve().parent
# Acessa a pasta raiz do projeto subindo dois níveis.
caminho_raiz_projeto = caminho_script.parent.parent
# Adiciona o caminho da raiz ao caminho de busca do Python.
sys.path.append(str(caminho_raiz_projeto))

# Assumindo que 'config' e os diretórios estão configurados
from config import DIRETORIO_DADOS_WEBSCRAPPING, DIRETORIO_DADOS_EXTRACAO_QA

# --- SELETORES HTML (CONSTANTES) ---
SELETOR_TITULO = 'h1'
SELETOR_CONTEUDO_POST = 'conversation-balloon__content__text'
SELETOR_COMENTARIOS_LISTA = 'comment-list__comment'
SELETOR_CONTEUDO_COMENTARIO = 'dell-comment-balloon__content'
SELETOR_ESPERA_CONTEUDO = (By.CLASS_NAME, 'conversation-balloon__content__text') 

# --- CONFIGURAÇÃO DE ARQUIVOS E CHECKPOINT ---
ARQUIVO_PROGRESSO = DIRETORIO_DADOS_WEBSCRAPPING / 'progresso_dell_community.txt'
caminho_entrada = DIRETORIO_DADOS_WEBSCRAPPING /'links_discussoes_Dell_Brasil.csv'
caminho_saida_perguntas = DIRETORIO_DADOS_EXTRACAO_QA / 'perguntas/posts_DellCommunity_Brasil_Perguntas.csv'
caminho_saida_respostas = DIRETORIO_DADOS_EXTRACAO_QA / 'respostas/comentarios_DellCommunity_Brasil_Respostas.csv'

# --- NOVOS ARQUIVOS PARA SALVAMENTO INCREMENTAL ---
ARQUIVO_TEMP_PERGUNTAS = DIRETORIO_DADOS_EXTRACAO_QA / 'perguntas/temp_posts_parcial.csv'
ARQUIVO_TEMP_RESPOSTAS = DIRETORIO_DADOS_EXTRACAO_QA / 'respostas/temp_comentarios_parcial.csv'

# Variáveis globais de status (usadas apenas para contagem e não compartilhadas)
LINKS_IGNORADOS = 0 

# Para garantir que a escrita no arquivo de progresso seja segura
progress_lock = mp.Lock() 

NOME_COLUNA_URL= 'Link da Discussão'

# --- FUNÇÕES DE CHECKPOINT (MANTIDAS) ---
def carregar_progresso():
    urls_processadas = set()
    if ARQUIVO_PROGRESSO.exists():
        with open(ARQUIVO_PROGRESSO, 'r', encoding='utf-8') as f:
            for line in f:
                urls_processadas.add(line.strip())
    return urls_processadas

def salvar_progresso(url):
    with progress_lock: 
        with open(ARQUIVO_PROGRESSO, 'a', encoding='utf-8') as f:
            f.write(url + '\n')

# --- NOVAS FUNÇÕES PARA SALVAMENTO INCREMENTAL ---
def salvar_dados_parciais(posts_data, comments_data, incremental=True):
    """
    Salva dados de forma incremental ou substitui arquivos temporários.
    """
    try:
        if posts_data:
            df_posts = pd.DataFrame(posts_data)
            if incremental and ARQUIVO_TEMP_PERGUNTAS.exists():
                # Modo append para salvar incrementalmente
                df_posts.to_csv(ARQUIVO_TEMP_PERGUNTAS, index=False, encoding='utf-8', mode='a', header=False)
            else:
                # Modo write (substitui ou cria novo)
                df_posts.to_csv(ARQUIVO_TEMP_PERGUNTAS, index=False, encoding='utf-8', mode='w', header=True)
                
        if comments_data:
            df_comments = pd.DataFrame(comments_data)
            if incremental and ARQUIVO_TEMP_RESPOSTAS.exists():
                df_comments.to_csv(ARQUIVO_TEMP_RESPOSTAS, index=False, encoding='utf-8', mode='a', header=False)
            else:
                df_comments.to_csv(ARQUIVO_TEMP_RESPOSTAS, index=False, encoding='utf-8', mode='w', header=True)
                
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar dados parciais: {e}")
        return False

def consolidar_dados_finais():
    """
    Consolida os dados temporários nos arquivos finais
    """
    try:
        # Consolidar posts
        if ARQUIVO_TEMP_PERGUNTAS.exists():
            df_temp_posts = pd.read_csv(ARQUIVO_TEMP_PERGUNTAS)
            df_temp_posts.to_csv(caminho_saida_perguntas, index=False, encoding='utf-8', 
                               mode='a', header=not caminho_saida_perguntas.exists())
            print(f"✅ Posts consolidados: {len(df_temp_posts)} registros")
            
        # Consolidar comentários
        if ARQUIVO_TEMP_RESPOSTAS.exists():
            df_temp_comments = pd.read_csv(ARQUIVO_TEMP_RESPOSTAS)
            df_temp_comments.to_csv(caminho_saida_respostas, index=False, encoding='utf-8',
                                  mode='a', header=not caminho_saida_respostas.exists())
            print(f"✅ Comentários consolidados: {len(df_temp_comments)} registros")
            
        # Limpar arquivos temporários
        ARQUIVO_TEMP_PERGUNTAS.unlink(missing_ok=True)
        ARQUIVO_TEMP_RESPOSTAS.unlink(missing_ok=True)
        
    except Exception as e:
        print(f"❌ Erro na consolidação final: {e}")

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
        
        # 2. Navegar para a URL
        driver.get(url)
        
        # 3. Esperar que o conteúdo principal esteja visível
        wait_selenium.until(EC.visibility_of_element_located(SELETOR_ESPERA_CONTEUDO))
        
        # Simula um scroll suave
        driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(random.uniform(0.5, 1.5)) 
        
        # 4. Extrair o HTML e processar com BeautifulSoup
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
        
        # 5. Salva o progresso IMEDIATAMENTE
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
    global LINKS_IGNORADOS
    start_time = time.time()
    
    links_para_processar = []
    urls_processadas_anteriormente = carregar_progresso()
    
    # Listas para acumular dados durante o processamento
    todos_posts_data = []
    todos_comments_data = []
    
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
            for index, row in enumerate(reader):
                url = row[NOME_COLUNA_URL].strip()
                
                if url in urls_processadas_anteriormente:
                    LINKS_IGNORADOS += 1
                    continue
                
                if url:
                    links_para_processar.append((url, index, driver_exec_path)) 
        
        TOTAL_LINKS_NA_SESSAO = len(links_para_processar)
        print(f"Links a processar nesta sessão: {TOTAL_LINKS_NA_SESSAO}. Links ignorados (já processados): {LINKS_IGNORADOS}.")

        if TOTAL_LINKS_NA_SESSAO == 0:
            print("Todos os links já foram processados. Saindo.")
            return

        # 3. Execução PARALELA usando mp.Pool com tqdm
        NUM_PROCESSOS = min(4, TOTAL_LINKS_NA_SESSAO)  # Não mais processos que links
        
        print(f"\n--- INICIANDO EXTRAÇÃO PARALELA com {NUM_PROCESSOS} processos ---")
        
        # Configuração para salvar a cada X links processados
        INTERVALO_SALVAMENTO = max(1, TOTAL_LINKS_NA_SESSAO // 10)  # Salva a cada ~10% do progresso
        
        # Limpa arquivos temporários anteriores se existirem
        ARQUIVO_TEMP_PERGUNTAS.unlink(missing_ok=True)
        ARQUIVO_TEMP_RESPOSTAS.unlink(missing_ok=True)
        
        with mp.Pool(processes=NUM_PROCESSOS) as pool:
            
            # Cria barra de progresso com tqdm
            with tqdm(total=TOTAL_LINKS_NA_SESSAO, desc="📊 Processando Links", 
                     unit="link", ncols=100, colour='green') as pbar:
                
                # Processa em chunks para salvar incrementalmente
                chunk_size = min(10, TOTAL_LINKS_NA_SESSAO)
                links_processados = 0
                
                for i in range(0, TOTAL_LINKS_NA_SESSAO, chunk_size):
                    chunk_links = links_para_processar[i:i + chunk_size]
                    
                    # Processa o chunk atual
                    results_chunk = []
                    for result in pool.starmap(worker_extrair_dados, chunk_links):
                        results_chunk.append(result)
                        pbar.update(1)  # Atualiza barra de progresso
                        links_processados += 1
                        
                        # Atualiza descrição com estatísticas em tempo real
                        sucessos = sum(1 for r in results_chunk if r[1])
                        taxa_sucesso = (sucessos / len(results_chunk)) * 100 if results_chunk else 0
                        pbar.set_postfix({
                            'Sucesso': f'{taxa_sucesso:.1f}%',
                            'Processados': f'{links_processados}/{TOTAL_LINKS_NA_SESSAO}'
                        })
                    
                    # Processa resultados do chunk
                    chunk_posts = []
                    chunk_comments = []
                    for url, success, post_data_list, comments_list in results_chunk:
                        if success:
                            chunk_posts.extend(post_data_list)
                            chunk_comments.extend(comments_list)
                    
                    # Acumula dados
                    todos_posts_data.extend(chunk_posts)
                    todos_comments_data.extend(chunk_comments)
                    
                    # SALVAMENTO INCREMENTAL
                    if chunk_posts or chunk_comments:
                        if salvar_dados_parciais(chunk_posts, chunk_comments, incremental=True):
                            print(f"💾 Dados salvos incrementalmente ({len(chunk_posts)} posts, {len(chunk_comments)} comentários)")
                    
                    # Estimativa de tempo restante
                    tempo_decorrido = time.time() - start_time
                    links_por_segundo = links_processados / tempo_decorrido if tempo_decorrido > 0 else 0
                    tempo_restante = (TOTAL_LINKS_NA_SESSAO - links_processados) / links_por_segundo if links_por_segundo > 0 else 0
                    
                    if tempo_restante > 0:
                        pbar.set_description(f"📊 Processando (ETA: {tempo_restante/60:.1f} min)")
                    
                    # Pequena pausa entre chunks para evitar sobrecarga
                    time.sleep(1)
        
        # Processa todos os resultados finais
        success_count = sum(1 for result in results_chunk if result[1]) if 'results_chunk' in locals() else 0
        
    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_entrada}' não foi encontrado.")
        
    except Exception as e:
        print(f"Ocorreu um erro durante a execução principal: {e}")
        traceback.print_exc()

    # 4. CONSOLIDAÇÃO FINAL
    print("\n--- Consolidando dados finais ---")
    consolidar_dados_finais()

    end_time = time.time()
    total_duration = end_time - start_time
    taxa = success_count / total_duration if total_duration > 0 and success_count > 0 else 0 
    
    print(f"\n🎉 Processo concluído!")
    print(f"⏱️  Duração total: {total_duration/60:.2f} minutos")
    print(f"✅ Links processados com sucesso: {success_count}/{TOTAL_LINKS_NA_SESSAO}")
    print(f"📈 Taxa média: {taxa:.2f} links/segundo")
    print(f"💾 Dados salvos em: {caminho_saida_perguntas.name} e {caminho_saida_respostas.name}")

if __name__ == "__main__":
    main()