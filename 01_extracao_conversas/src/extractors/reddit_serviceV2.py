import praw
import datetime
import time
import configparser
from pathlib import Path
from core_extration.base_extractor import BaseExtractor

class RedditService(BaseExtractor):
    def __init__(self):
        super().__init__(platform="reddit")
        
        # Carregamento das credenciais do praw.ini
        caminho_ini: Path = self.root_dir / "src/extractors/praw.ini"
        config_pra = configparser.ConfigParser()
        
        if not caminho_ini.exists():
            raise FileNotFoundError(f"Arquivo praw.ini não encontrado em: {caminho_ini}")
            
        config_pra.read(caminho_ini, encoding='utf-8')

        try:
            self.reddit = praw.Reddit(
                client_id=config_pra['DEFAULT']['client_id'],
                client_secret=config_pra['DEFAULT']['client_secret'],
                user_agent=config_pra['DEFAULT']['user_agent']
            )
            # Carrega parâmetros do seu JSON: search_groups, subreddits, etc.
            self.params = self.config["reddit_params"]
        except Exception as e:
            raise Exception(f"Falha na conexão com a API do Reddit: {e}")

    def consultar_limites_api(self):
        """Monitora a saúde da cota de requisições."""
        stats = self.reddit.auth.limits
        return {
            "restante": stats.get('remaining'),
            "reset_em": stats.get('reset_timestamp')
        }

    def buscar_modelo(self, modelo_busca, time_filter="year"):
        lista_posts = []
        ids_processados = set()
        subreddits = self.reddit.subreddit(self.params["subreddits"])
        
        for categoria, termos in self.params["search_groups"].items():
            termos_query = " OR ".join([f'"{t}"' for t in termos])
            query = f'{modelo_busca} ({termos_query})'
            
            tentativas = 10
            sucesso = False
            
            while tentativas > 0 and not sucesso:
                try:
                    print(f"    🔍 Categoria [{categoria}]: {query}")
                    search_results = subreddits.search(query, limit=100, time_filter=time_filter)
                    
                    for post in search_results:
                        if post.id in ids_processados or post.over_18:
                            continue
                        
                        post.comments.replace_more(limit=0)
                        
                        # 1. 🕒 TIMESTAMP DO COMENTÁRIO (Float puro do PRAW)
                        comentarios = [{
                            "id": comment.id,
                            "conteudo": comment.body,
                            "score": comment.score,
                            "data_comentario": datetime.datetime.fromtimestamp(
                                comment.created_utc
                            ).timestamp() # Unix Timestamp (Ex: 1717651200.0)
                        } for comment in post.comments.list()]

                        comentarios = sorted(comentarios, key=lambda x: x['score'], reverse=True)

                        # 2. 🕒 TIMESTAMP DO POST (Float puro do PRAW)
                        lista_posts.append({
                            "id": post.id,
                            "titulo": post.title,
                            "conteudo_post": post.selftext,
                            "subreddit": post.subreddit.display_name,
                            "flair": post.link_flair_text, # Nem sempre vai ser útil
                            "score": post.score,
                            "upvote_ratio": post.upvote_ratio,
                            "num_comments": post.num_comments,
                            "categoria": categoria,
                            "url": f"https://reddit.com{post.permalink}",
                            # Removido strftime para manter o dado numérico
                            "data_post": datetime.datetime.fromtimestamp(
                                post.created_utc).timestamp(), 
                            "comentarios": comentarios
                        })
                        ids_processados.add(post.id)
                    
                    sucesso = True
                    
                except Exception as e:
                    if "429" in str(e):
                        print(f"    🛑 Rate Limit (429). Dormindo 40s...")
                        time.sleep(40)
                        tentativas -= 1
                    else:
                        print(f"    ⚠️ Erro na categoria {categoria}: {e}")
                        break

        return lista_posts