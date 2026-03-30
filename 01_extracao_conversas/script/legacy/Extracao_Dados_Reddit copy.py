import sys
import json
import time
import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
import praw

# --- 1. CONFIGURAÇÕES E CAMINHOS ---
caminho_script = Path(__file__).resolve().parent
caminho_raiz_projeto = caminho_script.parent.parent 
sys.path.append(str(caminho_raiz_projeto))

try:
    from config import DIRETORIO_CSV_DATASET_FINAL, DIRETORIO_DADOS_EXTRACAO_QA
    from modelo_de_busca import ler_e_filtrar_modelos
except ImportError:
    print("Aviso: Módulos de configuração não encontrados. Usando caminhos locais.")
    DIRETORIO_CSV_DATASET_FINAL = caminho_script / 'dados_entrada'
    DIRETORIO_DADOS_EXTRACAO_QA = caminho_script / 'dados_saida'
    def ler_e_filtrar_modelos(caminho, marca, tipo): return []

CAMINHO_ENTRADA_CSV = DIRETORIO_CSV_DATASET_FINAL / 'dataset_laptops_GAMER_ONLY.csv'
CAMINHO_SAIDA_JSON = DIRETORIO_DADOS_EXTRACAO_QA / 'reddit_dados_estruturados_modelo.json'

# --- 2. PARÂMETROS DE BUSCA ---
QTD_LIMITE_POSTS_POR_KEYWORD = 100 # Reduzi um pouco para não estourar API rápido, já que faremos várias buscas
SUBREDDITS_ALVO = "all"

# Lista de termos para concatenar com o modelo
# A string vazia "" garante que a busca original (só o modelo) também seja feita
PALAVRAS_CHAVE = [
    "",             # Busca geral (só o modelo)
    "undervolt",
    "thermal",
    "overheating",
    "temperature",
    "battery",
    "screen",
    "fan",
    "bios",
    "driver",
    "crash",
    "blue screen",
    "fps drop"
]

# --- 3. AUTENTICAÇÃO PRAW ---
try:
    reddit = praw.Reddit(
        client_id='qgrpjfyUUZNPAp0wCymcdQ',
        client_secret='WshvOFWLM2YV5Rq87GRP-xwCwQoXPA',
        user_agent='ResearchTopic_TCC_Script/1.3_Keywords' 
    )
    print(f"Autenticação PRAW: OK (Read-Only: {reddit.read_only})")
except Exception as e:
    print(f"Erro Crítico de Autenticação: {e}")
    sys.exit()

# --- 4. FUNÇÕES UTILITÁRIAS ---

def unix_to_iso(timestamp):
    if not timestamp: return None
    return datetime.datetime.fromtimestamp(timestamp).isoformat()

def carregar_json_existente(caminho):
    if caminho.exists() and caminho.stat().st_size > 0:
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def exibir_ranking_subreddits(resultados_brutos, modelo):
    if not resultados_brutos:
        return

    lista_subs = [post.subreddit.display_name for post, _ in resultados_brutos]
    ranking = Counter(lista_subs).most_common(5) # Top 5 apenas para não poluir

    print(f"\n📊 RANKING (TOP 5) PARA: '{modelo}' (Total unificado: {len(resultados_brutos)})")
    print(f"{'Subreddit':<25} | {'Posts':<5}")
    print("-" * 35)
    
    for sub, qtd in ranking:
        print(f"r/{sub:<23} | {qtd:<5}")
    print("-" * 35 + "\n")

def processar_submission(submission):
    autor_post = "[Usuário Deletado]" or "[Deletado]"
    try:
        if submission.author:
            autor_post = submission.author.name
    except:
        pass

    lista_comentarios = []
    try:
        submission.comments.replace_more(limit=0) # Limit 0 é mais rápido para dataset massivo, mas pode aumentar se precisar
        for comment in submission.comments.list():
            if hasattr(comment, 'body'):
                autor_com = "[Deletado]"
                if hasattr(comment, 'author') and comment.author:
                    autor_com = comment.author.name
                    
                lista_comentarios.append({
                    "id_comentario": comment.id,
                    "autor_comentario": autor_com,
                    "conteudo": comment.body,
                    "score": comment.score,
                    "data_publicacao": unix_to_iso(comment.created_utc)
                })
    except Exception as e:
        print(f" [!] Erro ao ler comentários: {e}")

    return {
        "id_post": submission.id,
        "subreddit": submission.subreddit.display_name,
        "autor_post": autor_post,
        "titulo": submission.title,
        "url_original": submission.url,
        "conteudo_texto": submission.selftext,
        "score": submission.score,
        "proporcao_upvote": submission.upvote_ratio,
        "data_publicacao": unix_to_iso(submission.created_utc),
        "total_comentarios": submission.num_comments,
        "comentarios": lista_comentarios 
    }

def salvar_dados_json(buffer_dados, caminho_arquivo):
    if not buffer_dados: return

    print(f"\n[IO] Salvando {len(buffer_dados)} posts no JSON...")
    caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
    
    dados_existentes = carregar_json_existente(caminho_arquivo)
    
    novos_mapa = {}
    for sub, modelo in buffer_dados:
        if modelo not in novos_mapa: novos_mapa[modelo] = []
        novos_mapa[modelo].append(processar_submission(sub))

    data_atual = datetime.datetime.now().isoformat()

    for modelo, posts_estruturados in novos_mapa.items():
        encontrado = False
        for entry in dados_existentes:
            if entry.get("meta_data", {}).get("termo_pesquisado") == modelo:
                # Antes de adicionar, verificar duplicatas no JSON existente (opcional mas recomendado)
                ids_existentes = {p['id_post'] for p in entry['posts']}
                posts_filtrados = [p for p in posts_estruturados if p['id_post'] not in ids_existentes]
                
                entry["posts"].extend(posts_filtrados)
                encontrado = True
                break
        
        if not encontrado:
            dados_existentes.append({
                "meta_data": {
                    "fonte": "Reddit",
                    "subreddits": SUBREDDITS_ALVO,
                    "data_extracao": data_atual,
                    "termo_pesquisado": modelo
                },
                "posts": posts_estruturados
            })

    try:
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_existentes, f, ensure_ascii=False, indent=4)
        print(" -> JSON atualizado.")
    except Exception as e:
        print(f" [X] Erro IO: {e}")

# --- 5. BUSCA OTIMIZADA COM KEYWORDS ---
def buscar_modelo_com_variacoes(modelo):
    """
    Realiza várias buscas combinando o modelo com palavras-chave.
    Remove duplicatas (posts que aparecem em mais de uma busca).
    """
    posts_unicos = {} # Dicionário id_post -> objeto submission
    
    print(f"🔍 Iniciando varredura para: {modelo}")
    
    for keyword in PALAVRAS_CHAVE:
        # Monta a query: "Modelo Exato" keyword
        # Ex: "Dell G7 7588" undervolt
        termo = f'""{modelo}"" {keyword}'.strip()
        
        try:
            print(f"   -> Buscando: {termo}...") # Descomente se quiser ver o log detalhado
            referencia = reddit.subreddit(SUBREDDITS_ALVO).search(
                termo, sort="relevance", limit=QTD_LIMITE_POSTS_POR_KEYWORD
            )
            
            for post in referencia:
                if post.id not in posts_unicos:
                    posts_unicos[post.id] = post
                    
        except Exception as e:
            print(f"   [!] Erro na keyword '{keyword}': {e}")
            continue
            
    lista_final = list(posts_unicos.values())
    print(f"   -> Total unificado encontrado para {modelo}: {len(lista_final)} posts.")
    
    # Retorna lista de tuplas para manter compatibilidade com o resto do código
    return [(post, modelo) for post in lista_final]

# --- 6. MAIN ---
def main():
    print("\n=== EXTRATOR REDDIT MULTI-KEYWORD ===")
    opcao = input("1. CSV | 2. Manual: ").strip()
    lista = []

    if opcao == '2':
        entrada = input("Hardware (ex: Dell G7 15 7588): ").strip()
        if entrada: lista = [entrada]
    else:
        try:
            lista = ler_e_filtrar_modelos(CAMINHO_ENTRADA_CSV, None, 'Gamer')
        except:
            print("Erro CSV.")
            sys.exit()

    if not lista: sys.exit()

    buffer = []
    # Reduzi max_workers pois agora cada thread faz ~10 requisições (loops de keywords)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(buscar_modelo_com_variacoes, m) for m in lista]
        
        for i, f in enumerate(as_completed(futures), 1):
            resultado_thread = f.result()
            
            if resultado_thread:
                modelo_atual = resultado_thread[0][1]
                exibir_ranking_subreddits(resultado_thread, modelo_atual)
            
            buffer.extend(resultado_thread)
            
            # Salva a cada 1 modelo processado (pois agora cada modelo traz muito mais dados)
            if i % 1 == 0:
                salvar_dados_json(buffer, CAMINHO_SAIDA_JSON)
                buffer.clear()

    salvar_dados_json(buffer, CAMINHO_SAIDA_JSON)
    print("\nConcluído.")

if __name__ == "__main__":
    main()