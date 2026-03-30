# Regex de Hardware (Versão Definitiva 2010-2026)
# Este arquivo contém apenas os dados de referência.

PADROES_HARDWARE = {
    # GPU: NVIDIA (GeForce/Quadro/Titan), AMD (Radeon/Pro/Instinct), INTEL (Arc)
    "gpu": r"\b("
           r"(geforce\s*)?(rtx|gtx|gt|mx|quadro|titan)\s*\d{3,4}[a-z0-9]*([\s-]*(ti|super|max-q|mobile|oc|ada|lhr|ultra))?|" 
           r"(amd\s*)?(radeon\s*(tm|™)?\s*)?(rx|r9|r7|r5|hd|vega)\s*(\d{3,4}|[a-z0-9]+)([\s-]*(xt|xtx|gre|m|xt-m|pro|xtr))?|" 
           r"(intel\s*)?(arc)\s*[ab]\d{3,4}[a-z]*|" 
           r"iris\s*xe|uhd\s*graphics|radeon\s*graphics" 
           r")\b",
    
    # CPU: INTEL & AMD (Incluindo novas nomenclaturas Core Ultra e Ryzen AI)
    "cpu": r"\b("
           r"(intel\s*)?(core\s*(ultra)?\s*)?(i[3579]|[3579])[\s-]*\d{3,5}[a-z0-9]*|" 
           r"(intel\s*)?(pentium|celeron|atom|xeon)[\s-]*[a-z0-9]+|" 
           r"(amd\s*)?(ryzen\s*(threadripper|ai)?\s*[3579]|athlon|fx|a[468]|a1[02])[\s-]*(\d{3,4}[a-z]*)?" 
           r")\b",
    
    # STORAGE: SSD (NVMe/SATA) & HDD (Marcas + RPM)
    "storage": r"\b("
               r"(\d{1,4}\s*(gb|tb)\s*)?" 
               r"(" 
                   r"(samsung|wd|western\s*digital|crucial|kingston|sandisk|seagate|toshiba|sk\s*hynix|hynix|corsair|sabrent|adata|xpg|pny|lexar|hp|intel|teamgroup|patriot|gigabyte|hgst|hitachi)|" 
                   r"(firecuda|barracuda|ironwolf|skyhawk|exos|blue|black|green|red|purple|gold|ultrastar|p300|x300|n300|l200|evo|qvo|pro|plus|mx500|bx500|p3|p5|nv2|kc3000|fury|legend|gammix|sn\d{3,4})" 
               r")?\s*"
               r"([a-z0-9-]+\s*)?" 
               r"(ssd|nvme|m\.2|sata|hdd|hard\s*drive|disco\s*r[ií]gido|hd|sshd|sdd|7200\s*rpm|5400\s*rpm)" 
               r"(\s*\d{1,4}\s*(gb|tb))?" 
               r")\b",
    
    # RAM: Detalhada (Marca + Linha + Capacidade + Tecnologia + Velocidade)
    "ram": r"\b("
           r"((128|64|32|16|8|4|2)\s*gb\s*(x\d|2x|1x)?\s*)?" 
           r"(" 
               r"(corsair|kingston|crucial|g\.?skill|samsung|sk\s*hynix|hynix|adata|teamgroup|patriot|hyperx|micron|pny|transcend|geil|mushkin|t-force|klevv)|" 
               r"(vengeance|fury|beast|impact|ballistix|trident|ripjaws|viper|dominator|elite|value\s*ram|aorus|predator|vulcan)" 
           r")?\s*"
           r"([a-z0-9-]+\s*)?" 
           r"(ddr[2-5]|lpddr[3-5]x?|sodimm|so-dimm|dimm|udimm|ram|mem[oó]ria)" 
           r"(\s*\d{3,5}\s*(mhz|mt/s)?)?" 
           r"(\s*cl\d{1,2})?" 
           r"(\s*(128|64|32|16|8|4|2)\s*gb)?" 
           r")\b",
    
    # TELA: Painéis e Resoluções
    "screen": r"\b("
              r"\d{2,3}(\.\d)?[\"”]\s*|"
              r"120hz|144hz|165hz|240hz|300hz|360hz|480hz|60hz|"
              r"ips|tn|va|wva|pls|oled|amoled|miniled|mini-led|retina|"
              r"4k|uhd|qhd|wqhd|fhd|hd\+|full\s*hd|1080p|1440p|2160p|768p|1366x768|1920x1080"
              r")\b"
}