import re
import html
import json
from datetime import datetime

class TextCleanerServiceV3:
    # Mapeamento expandido para RAG Semântico
    ACRONYM_MAP = {
        # Diagnóstico e Performance (Novos achados)
        r'\blatency-mon\b': 'LatencyMon (DPC/ISR latency diagnostic tool)',
        r'\bdpc\b': 'deferred procedure call (system latency issue)',
        r'\bmux\b': 'multiplexer switch (dedicated GPU toggle)',
        r'\bthrottling\b': 'thermal performance limitation',
        r'\bstuttering\b': 'frame time inconsistency (stuttering)',
        
        # Firmware e Energia
        r'\bacpi\b': 'advanced configuration and power interface (firmware)',
        r'\bec\b': 'embedded controller (power management firmware)',
        r'\bvoltage\b': 'CPU/GPU voltage (related to undervolting/heat)',
        r'\bpd\b': 'USB-C power delivery charging',
        
        # Soluções e Materiais (Expandido com PTM7958)
        r'\bptm7950\b': 'Honeywell PTM7950 phase change thermal material',
        r'\bptm7958\b': 'Honeywell PTM7958 phase change thermal paste',
        r'\brepaste\b': 'thermal paste replacement',
        r'\bundervolt\b': 'voltage reduction to decrease heat',
        
        # Hardware Específico
        r'\bvram\b': 'video random access memory',
        r'\bxmp\b': 'extreme memory profile (RAM optimization)',
    }

    @staticmethod
    def limpar_preservando_tecnico(texto: str):
        if not texto or not isinstance(texto, str): return ""
        try:
            texto = html.unescape(texto)
        except: pass
        
        # 1. Remover Ruído Social (Bots e URLs)
        texto = re.sub(r'https?://\S+|www\.\S+', ' ', texto)
        texto = re.sub(r'\b[ur]/[A-Za-z0-9_]+\b', ' ', texto)
        
        # 2. Expansão de Acrônimos
        for pattern, replacement in TextCleanerServiceV3.ACRONYM_MAP.items():
            texto = re.sub(pattern, replacement, texto, flags=re.IGNORECASE)

        # 3. Normalização (Preservando símbolos técnicos como °C, GHz, etc)
        texto = re.sub(r"[^\w\s.,!?\-°CghzMHzvVwW%]", ' ', texto)
        return ' '.join(texto.split())

    @staticmethod
    def validar_e_limpar(texto: str, categoria: str, grupos_pesquisa: dict):
        texto_limpo = TextCleanerServiceV3.limpar_preservando_tecnico(texto)
        keywords = grupos_pesquisa.get(categoria, [])
        termos_encontrados = [k for k in keywords if k.lower() in texto_limpo.lower()]
        return texto_limpo, termos_encontrados

    @staticmethod
    def extrair_versoes(texto: str):
        """Captura drivers e BIOS (Ex: 535.88, v1.02)"""
        return re.findall(r'\b\d{2,3}\.\d{2,3}\b|v\d+\.\d+|\bBIOS\s\w+\b', texto)

class TemporalRAGManager:
    @staticmethod
    def ancorar_data(unix_timestamp):
        """Data ISO 8601 para consciência temporal do RAG"""
        return datetime.fromtimestamp(unix_timestamp).isoformat()

class TechnicalFilterV2:
    def __init__(self, settings_path="extractor_settings_extendedV2.json"):
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        self.grupos = settings['reddit_params']['search_groups']
        self.cleaner = TextCleanerServiceV3()
        self.temporal = TemporalRAGManager()

    def avaliar_v2(self, post, marca, modelo):
        """Processamento completo para RAG."""
        categoria = post.get('categoria', 'general')
        texto_base = f"{post.get('titulo', '')} {post.get('conteudo_post', '')}"
        
        # Limpeza e Validação de Categoria
        texto_limpo, keywords = self.cleaner.validar_e_limpar(texto_base, categoria, self.grupos)
        
        # Ancoragem Temporal
        data_iso = self.temporal.ancorar_data(post.get('data_post', 0))
        
        # Versões
        versoes = self.cleaner.extrair_versoes(texto_limpo)
        
        # Relevância básica (Simulando lógica da classe pai)
        relevante = any(k in texto_limpo.lower() for k in [marca.lower(), modelo.lower()]) or len(keywords) > 0

        return {
            "manter": relevante,
            "texto_limpo": texto_limpo,
            "data_rag": data_iso,
            "metadados": {
                "versoes": versoes,
                "keywords_tecnicas": keywords,
                "categoria_confirmada": len(keywords) > 0
            }
        }