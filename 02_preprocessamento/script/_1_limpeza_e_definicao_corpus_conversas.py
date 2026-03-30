import os
import json
import re
from core.paths import EXTRACAO_DATA_BRUTO, PREPROCESSAMENTO_DATA

CAMINHO_ENTRADA = EXTRACAO_DATA_BRUTO
CAMINHO_SAIDA = PREPROCESSAMENTO_DATA / "Dados_Limpos_Iniciais"

def limpar_texto_conservador(texto):
    if not texto: return ""
    texto = re.sub(r'http\S+|www\S+|https\S+', '', texto, flags=re.MULTILINE)
    texto = texto.replace('\t', ' ')
    texto = re.sub(r'\n+', ' ', texto) 
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def eh_ruido_real(autor, conteudo):
    if not conteudo or len(str(conteudo).strip()) < 2: return True
    autor_str = str(autor).lower() if autor else ""
    conteudo_str = str(conteudo).lower()
    bots = ["automoderator", "visualmod", "remindmebot"]
    if any(bot in autor_str for bot in bots): return True
    if conteudo_str.strip() in ["[deleted]", "[removed]"]: return True
    return False

def executar_limpeza():
    if not os.path.exists(CAMINHO_SAIDA): os.makedirs(CAMINHO_SAIDA)
    arquivos = [f for f in os.listdir(CAMINHO_ENTRADA) if f.endswith('.json')]
    
    for arquivo in arquivos:
        with open(CAMINHO_ENTRADA / arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        posts_limpos = []
        ids_locais = set()

        for post in dados.get('posts', []):
            if post.get('id') in ids_locais or eh_ruido_real(post.get('author'), post.get('conteudo_post')):
                continue
            
            comentarios_ok = []
            for coment in post.get('comentarios', []):
                if not eh_ruido_real(coment.get('autor'), coment.get('conteudo')):
                    txt = limpar_texto_conservador(coment.get('conteudo'))
                    if len(txt) > 2:
                        coment['conteudo'] = txt
                        comentarios_ok.append(coment)

            post['titulo'] = limpar_texto_conservador(post.get('titulo'))
            post['conteudo_post'] = limpar_texto_conservador(post.get('conteudo_post'))
            post['comentarios'] = comentarios_ok
            posts_limpos.append(post)
            ids_locais.add(post.get('id'))

        dados['posts'] = posts_limpos
        with open(CAMINHO_SAIDA / arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    executar_limpeza()