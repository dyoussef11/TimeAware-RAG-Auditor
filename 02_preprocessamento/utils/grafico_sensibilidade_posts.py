import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from core.paths import PREPROCESSAMENTO_DATA, EXTRACAO_DATA

# Configuração de Caminhos
# Buscamos o CSV gerado anteriormente na pasta de Contagem
CAMINHO_INPUT = EXTRACAO_DATA / "Contagem_Analise" / "prevalencia_com_comentarios.csv"
# Pasta sugerida para a análise de sensibilidade
CAMINHO_SAIDA = PREPROCESSAMENTO_DATA / "Analise_Sensibilidade"

def gerar_grafico_sensibilidade():
    # 1. Criar a pasta de saída se não existir
    if not os.path.exists(CAMINHO_SAIDA):
        os.makedirs(CAMINHO_SAIDA)
        print(f"Diretório criado: {CAMINHO_SAIDA}")

    try:
        # 2. Carregar os dados de prevalência
        df = pd.read_csv(CAMINHO_INPUT, sep=';', encoding='utf-8-sig')
        
        # 3. Calcular a sensibilidade para diferentes níveis de Threshold
        thresholds = range(1, 51) # Testa de 1 a 50 posts mínimos
        resultados = []
        total_posts_global = df['posts_unicos'].sum()

        for t in thresholds:
            mask = df['posts_unicos'] >= t
            modelos_mantidos = df[mask].shape[0]
            posts_cobertos = df[mask]['posts_unicos'].sum()
            representatividade = (posts_cobertos / total_posts_global) * 100
            
            resultados.append({
                "Threshold": t,
                "Modelos": modelos_mantidos,
                "Representatividade": representatividade
            })

        df_sens = pd.DataFrame(resultados)

        # 4. Configurar o visual do gráfico
        sns.set_theme(style="whitegrid")
        fig, ax1 = plt.subplots(figsize=(12, 7))

        # Eixo Esquerdo: Quantidade de Modelos (Linha Vermelha)
        color = 'tab:red'
        ax1.set_xlabel('Threshold (Mínimo de Posts por Modelo)', fontsize=12)
        ax1.set_ylabel('Quantidade de Modelos Restantes', color=color, fontsize=12)
        sns.lineplot(x='Threshold', y='Modelos', data=df_sens, ax=ax1, color=color, marker='o', linewidth=2.5)
        ax1.tick_params(axis='y', labelcolor=color)

        # Eixo Direito: Representatividade da Base (Linha Azul)
        ax2 = ax1.twinx()
        color = 'tab:blue'
        ax2.set_ylabel('Representatividade do Corpus (%)', color=color, fontsize=12)
        sns.lineplot(x='Threshold', y='Representatividade', data=df_sens, ax=ax2, color=color, linestyle='--', alpha=0.6)
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.set_ylim(90, 101) # Foca na parte alta da representatividade

        # 5. Destaque para o Ponto de Threshold 20 (Justificativa Visual)
        plt.axvline(x=20, color='black', linestyle=':', alpha=0.7)
        plt.text(21, 95, 'Threshold Sugerido (N=20)', verticalalignment='center', fontweight='bold')

        plt.title('Análise de Sensibilidade para Definição de Threshold de Amostragem', fontsize=15, pad=20)
        
        # 6. Salvar a imagem
        nome_arquivo = "grafico_sensibilidade_threshold.png"
        caminho_final = CAMINHO_SAIDA / nome_arquivo
        plt.tight_layout()
        plt.savefig(caminho_final, dpi=300)
        
        print(f"--- Sucesso ---")
        print(f"Gráfico salvo em: {caminho_final}")
        print(f"Modelos com Threshold 20: {df_sens.loc[df_sens['Threshold']==20, 'Modelos'].values[0]}")
        print(f"Representatividade mantida: {df_sens.loc[df_sens['Threshold']==20, 'Representatividade'].values[0]:.2f}%")

    except Exception as e:
        print(f"Erro ao gerar análise de sensibilidade: {e}")

if __name__ == "__main__":
    gerar_grafico_sensibilidade()