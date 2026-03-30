import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from core.paths import EXTRACAO_DATA

# Configurações de caminhos
CAMINHO_PASTA = EXTRACAO_DATA / "Contagem_Analise"
ARQUIVO_COM = CAMINHO_PASTA / "prevalencia_com_comentarios.csv"
ARQUIVO_ZERO = CAMINHO_PASTA / "prevalencia_zero_comentarios.csv"

def gerar_visualizacao_comparativa():
    try:
        # 1. Carregar os dados (Certifique-se que o script de análise gerou ambos)
        df_com = pd.read_csv(ARQUIVO_COM, sep=';', encoding='utf-8-sig')
        df_zero = pd.read_csv(ARQUIVO_ZERO, sep=';', encoding='utf-8-sig')

        # Adicionar coluna identificadora para o gráfico
        df_com['grupo'] = 'Ativos (Com Comentários)'
        df_zero['grupo'] = 'Silenciosos (Zero Comentários)'

        # Concatenar para análise global
        df_full = pd.concat([df_com, df_zero])
        temas = ["performance", "thermal", "energy", "display", "stability"]

        sns.set_theme(style="whitegrid")

        # --- GRÁFICO 1: Distribuição de Densidade Técnica (Violin Plot) ---
        # Corrigido: Adicionado hue='grupo' e legend=False para evitar warnings
        plt.figure(figsize=(10, 6))
        sns.violinplot(
            x='grupo', 
            y='densidade_tecnica', 
            data=df_full, 
            hue='grupo',
            palette='muted', 
            split=True,
            legend=False
        )
        plt.title('Comparativo de Riqueza Técnica: Ativos vs Silenciosos\n(Densidade de Termos Técnicos)', fontsize=14)
        plt.savefig(CAMINHO_PASTA / "04_comparativo_densidade_tecnica.png", dpi=300)
        plt.close()

        # --- GRÁFICO 2: Diversidade Temática (NOVO) ---
        # Mostra quantos temas diferentes cada grupo costuma cobrir
        plt.figure(figsize=(10, 6))
        sns.boxplot(
            x='grupo', 
            y='temas_cobertos', 
            data=df_full, 
            hue='grupo',
            palette='Set2',
            legend=False
        )
        plt.title('Diversidade de Assuntos (Quantidade de Temas por Modelo)', fontsize=14)
        plt.ylabel('Nº de Temas Diferentes (0 a 5)')
        plt.savefig(CAMINHO_PASTA / "05_comparativo_diversidade_temas.png", dpi=300)
        plt.close()

        # --- GRÁFICO 3: Top 20 Modelos por Volume ---
        top_20_modelos = df_com.sort_values(by='posts_unicos', ascending=False)['modelo'].head(20).tolist()
        df_top = df_full[df_full['modelo'].isin(top_20_modelos)]

        plt.figure(figsize=(14, 8))
        sns.barplot(
            x='posts_unicos', 
            y='modelo', 
            hue='grupo', 
            data=df_top, 
            order=top_20_modelos,
            palette='viridis'
        )
        plt.title('Top 20 Modelos: Volume de Posts Ativos vs. Silenciosos', fontsize=15)
        plt.xlabel('Quantidade de Posts Únicos')
        plt.tight_layout()
        plt.savefig(CAMINHO_PASTA / "06_top20_comparativo_volume.png", dpi=300)
        plt.close()

        # --- GRÁFICO 4: Perfil Temático Relativo (Stacked 100%) ---
        soma_temas = df_full.groupby('grupo')[temas].sum()
        soma_temas_pct = soma_temas.div(soma_temas.sum(axis=1), axis=0).fillna(0)

        soma_temas_pct.plot(kind='barh', stacked=True, figsize=(12, 5), cmap='Spectral')
        plt.title('Diferença de Assuntos: Ativos vs Silenciosos', fontsize=14)
        plt.xlabel('Proporção de Menções aos Temas')
        plt.legend(title="Temas", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(CAMINHO_PASTA / "07_perfil_tematico_comparado.png", dpi=300)
        plt.close()

        print(f"Sucesso! 4 Gráficos comparativos (incluindo Diversidade) gerados em: {CAMINHO_PASTA}")

    except Exception as e:
        print(f"Erro ao gerar gráficos comparativos: {e}")

if __name__ == "__main__":
    gerar_visualizacao_comparativa()