import json
from core.paths import EXTRACAO_DATA, EXTRACAO_DATA_BRUTO, NER_DATA

# Configurações de Caminho
CAMINHO_JSON = EXTRACAO_DATA_BRUTO /  'acer_acer16predatorneonh.qltsi.001_corei5_16.json'
ARQUIVO_SAIDA = EXTRACAO_DATA / 'arvore_json' / "ESTRUTURA_PROJETOV5.md"

def extrair_arvore(dados, indent="", prefixo="└── "):
    """Gera a representação visual em árvore recursivamente."""
    linhas = []
    
    # TRATAMENTO PARA LISTA NO TOPO DO JSON
    if isinstance(dados, list):
        if len(dados) > 0:
            linhas.append(f"{indent}└── [Lista de {type(dados[0]).__name__}]")
            linhas.extend(extrair_arvore(dados[0], indent + "    "))
        return linhas

    if isinstance(dados, dict):
        itens = list(dados.items())
        for i, (chave, valor) in enumerate(itens):
            e_ultimo = (i == len(itens) - 1)
            tipo = type(valor).__name__
            linhas.append(f"{indent}{prefixo}{chave} [{tipo}]")
            
            proximo_indent = indent + ("    " if e_ultimo else "│   ")
            if isinstance(valor, dict):
                linhas.extend(extrair_arvore(valor, proximo_indent))
            elif isinstance(valor, list) and len(valor) > 0:
                linhas.append(f"{proximo_indent}└── [Exemplo de item na lista: {type(valor[0]).__name__}]")
                if isinstance(valor[0], (dict, list)):
                    linhas.extend(extrair_arvore(valor[0], proximo_indent + "    "))
    return linhas

def extrair_tabela(dados, caminho_pai=""):
    """Mapeia os campos para uma tabela plana (dot notation)."""
    linhas = []
    
    # TRATAMENTO PARA LISTA NO TOPO DO JSON
    if isinstance(dados, list):
        if len(dados) > 0 and isinstance(dados[0], dict):
            linhas.extend(extrair_tabela(dados[0], caminho_pai + "[]" if caminho_pai else "root[]"))
        return linhas

    if isinstance(dados, dict):
        for chave, valor in dados.items():
            caminho_atual = f"{caminho_pai}.{chave}" if caminho_pai else chave
            tipo = type(valor).__name__
            linhas.append(f"| `{caminho_atual}` | `{tipo}` | |")
            
            if isinstance(valor, dict):
                linhas.extend(extrair_tabela(valor, caminho_atual))
            elif isinstance(valor, list) and len(valor) > 0:
                if isinstance(valor[0], dict):
                    linhas.extend(extrair_tabela(valor[0], f"{caminho_atual}[]"))
    return linhas

def salvar_markdown(dados, nome_saida):
    """Compila os dados e salva o arquivo .md final."""
    arvore_str = "\n".join(extrair_arvore(dados))
    tabela_str = "\n".join(extrair_tabela(dados))
    
    if not arvore_str:
        arvore_str = "Não foi possível mapear a árvore (JSON vazio ou formato inesperado)."
    
    conteudo = (
        f"# Estrutura do JSON: {CAMINHO_JSON.name}\n\n"
        "## 1. Hierarquia Visual\n"
        "```text\n"
        f"{arvore_str}\n"
        "```\n\n"
        "---\n\n"
        "## 2. Dicionário de Campos\n"
        "| Campo | Tipo | Descrição |\n"
        "| :--- | :--- | :--- |\n"
        f"{tabela_str}\n"
    )
    
    with open(nome_saida, "w", encoding="utf-8") as f:
        f.write(conteudo)

def main():
    """Execução principal do script."""
    try:
        print(f"Lendo arquivo: {CAMINHO_JSON}")
        with open(CAMINHO_JSON, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            
        print(f"Mapeando estrutura de {type(dados).__name__}...")
        salvar_markdown(dados, ARQUIVO_SAIDA)
        print(f"Sucesso! Documentação gerada em: {ARQUIVO_SAIDA}")

    except FileNotFoundError:
        print(f"Erro: O arquivo não foi encontrado em {CAMINHO_JSON}")
    except Exception as e:
        import traceback
        print(f"Erro inesperado: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()