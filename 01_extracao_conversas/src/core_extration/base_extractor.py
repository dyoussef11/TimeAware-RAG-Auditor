import json
from pathlib import Path


from core.paths import (

EXTRACAO_CONFIG, EXTRACAO

)

class BaseExtractor:
    def __init__(self, platform):
        self.platform = platform

        self.root_dir: Path = EXTRACAO
        self.config = self._load_config()
        self._setup_folders()

    def _load_config(self):
        
        config_path: Path = EXTRACAO_CONFIG / "extractor_settings_extendedV2.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f) 

    def _setup_folders(self):
        pasta_bruta: Path = self.root_dir / self.config["paths"]["output_bruto"]
        pasta_bruta.mkdir(parents=True, exist_ok=True)
        (self.root_dir / "logs").mkdir(exist_ok=True)