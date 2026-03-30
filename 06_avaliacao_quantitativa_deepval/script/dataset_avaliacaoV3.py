# dataset_avaliacaoV3.py

TEST_SUITE = [
    # =========================================================================
    # CATEGORIA 1: CONHECIMENTO ESTÁTICO (FAISS + TAGGING)
    # Testa se ele extrai specs corretas de um modelo existente na base.
    # =========================================================================
    {
        "id": "TC_STATIC_01",
        "input": "What is the maximum RAM capacity for the Acer Nitro 5 AN515-56?",
        "expected_output": "[RAG] The Acer Nitro 5 AN515-56 supports a maximum of 32GB DDR4 3200MHz RAM across its two SO-DIMM slots.",
        "expected_context": ["[INTENT: Technical Specifications] [YEAR: 2021] Acer Nitro 5 AN515-56: Memory support up to 32GB DDR4-3200, 2x slots available."] 
    },
    {
        "id": "TC_STATIC_02",
        "input": "How many M.2 SSD slots does the Acer Nitro 5 AN515-56 have?",
        "expected_output": "[RAG] This model features two M.2 SSD slots and one 2.5-inch SATA HDD bay for storage expansion.",
        "expected_context": ["[INTENT: Storage Specs] [YEAR: 2021] Acer Nitro 5 AN515-56 storage options: 2x M.2 PCIe NVMe slots and 1x 2.5\" SATA slot."] 
    },

    # =========================================================================
    # CATEGORIA 2: ANOMALIA TEMPORAL (Zero-Trust)
    # Testa se ele barra hardware lançado após a data de referência (Ex: RTX 50 series).
    # =========================================================================
    {
        "id": "TC_TEMPORAL_01",
        "input": "Can I run the new RTX 5060 Ti drivers on my Acer Nitro 5 AN515-56?",
        "reference_date": "2023-12-01",
        "expected_output": "[TIMELINE_ANOMALY] The RTX 5060 Ti is not available as of late 2023. [RAG] The AN515-56 is equipped with an NVIDIA GeForce RTX 3050 or 3050 Ti Laptop GPU.",
        "expected_context": ["[INTENT: GPU Specs] [YEAR: 2021] Acer Nitro 5 AN515-56 features NVIDIA RTX 3050 / 3050 Ti graphics."]
    },

    # =========================================================================
    # CATEGORIA 3: CONFLITO DE VERSÃO (HARDCORE TEMPORAL)
    # Testa se ele prioriza a informação mais recente (Reranking 4%/ano).
    # =========================================================================
    {
        "id": "TC_CONFLICT_01",
        "input": "Is there a firmware fix for the Nitro 5 AN515-56 screen flickering issue?",
        "reference_date": "2025-06-01",
        "expected_output": "[TIMELINE_ANOMALY] While early 2021 reports suggested hardware replacement, a 2024 firmware update (v1.12) resolved the flickering for most users. [RAG] Ensure you are on BIOS v1.12 or later.",
        "expected_context": [
            "[INTENT: BIOS Update] [YEAR: 2024] BIOS v1.12: Optimized panel power management to resolve intermittent flickering.",
            "[INTENT: User Complaint] [YEAR: 2021] My Nitro 5 AN515-56 screen flickers; Acer support says it needs a screen replacement."
        ]
    },

    # =========================================================================
    # CATEGORIA 4: SKU MISMATCH (Precisão Cirúrgica)
    # Testa se ele diferencia o AN515-56 (Intel 11th) do AN515-57 (Intel 11th + Novos Ports).
    # =========================================================================
    {
        "id": "TC_SKU_01",
        "input": "Does my Acer Nitro 5 AN515-56 support Thunderbolt 4?",
        "expected_output": "[SKU MISMATCH] [RAG] No. The AN515-56 features USB 3.2 Gen 2 (Type-C). Thunderbolt 4 is typically found on the higher-end Predator Helios series or specific AN515-57 variants.",
        "expected_context": [
            "[INTENT: I/O Ports] [YEAR: 2021] Acer Nitro 5 AN515-56: 1x USB Type-C 3.2 Gen 2, 3x USB Type-A.",
            "[INTENT: Feature Comparison] [YEAR: 2021] Comparison: AN515-57 adds Thunderbolt 4 support on select regions."
        ]
    },

    # =========================================================================
    # CATEGORIA 5: HÍBRIDO (RAG + INTERNAL)
    # Mistura dados reais do Acer com conhecimento geral de hardware.
    # =========================================================================
    {
        "id": "TC_HYBRID_01",
        "input": "What is the benefit of the dual-fan design in the Nitro 5 AN515-56?",
        "expected_output": "[RAG] The Nitro 5 uses dual fans and quad exhaust ports. [INTERNAL] This design increases airflow and heat dissipation efficiency during high-load gaming sessions. Source: General Hardware Knowledge.",
        "expected_context": ["[INTENT: Cooling System] Acer Nitro 5 (2021) employs a dual-fan, quad-exhaust thermal layout."]
    },

    {
    "id": "TC_TIME_01",
    "input": "What is the latest stable BIOS version for the Helios Neo 16 as of 2026?",
    "expected_output": "[RAG] The latest version is v2.10 (Feb 2026), which fixes the freezing issues reported in earlier 2024 versions.",
    "expected_context": [
        "TIMELINE: 2026-02. MODEL: acer 16 predator neo. FAULT: Random freezing. RESOLUTION: Update to BIOS v2.10."
    ]
    },

    {
        "id": "TC_TIME_SENS_01_ACTIVE",
        "input": "My Nitro 5 was purchased in Jan 2024. Is the standard 12-month warranty still active?",
        "reference_date": "2024-08-01",
        "expected_output": "[RAG] Yes, your warranty is active until January 2025. [INTERNAL] Standard manufacturer warranties typically last 12 months from the invoice date. Source: General Hardware Knowledge.",
        "expected_context": ["[YEAR: 2024] Acer Warranty Policy: 12 months standard coverage for Nitro series."]
    },
    {
        "id": "TC_TIME_SENS_01_EXPIRED",
        "input": "My Nitro 5 was purchased in Jan 2024. Is the standard 12-month warranty still active?",
        "reference_date": "2026-03-24", # Data de "Hoje" no sistema
        "expected_output": "[RAG] No, your standard warranty expired in January 2025. [INTERNAL] You may check for extended warranty plans if available. Source: General Hardware Knowledge.",
        "expected_context": ["[YEAR: 2024] Acer Warranty Policy: 12 months standard coverage for Nitro series."]
    },

    # =========================================================================
    # CATEGORIA 2: CONFLITO DE RECÊNCIA (O "DUELO" DE VERDADE)
    # Testa se o decaimento temporal (4%/ano) ou a lógica do V8 prioriza o dado novo.
    # =========================================================================
    {
        "id": "TC_RECENCY_CONFLICT_01",
        "input": "What is the maximum RAM for the Nitro 5 AN515-56?",
        "reference_date": "2026-01-01",
        "expected_output": "The Nitro 5 AN515-56 supports up to 64GB of DDR4 RAM following the BIOS update v2.04 released in 2024. For optimal stability and dual-channel performance, it is recommended to use identical memory modules.",
        "expected_context": [
            "[YEAR: 2021] Official Spec Sheet: Max RAM 32GB DDR4.",
            "[YEAR: 2024] BIOS Update v2.04: Expanded memory controller compatibility to support 64GB kits (2x32GB)."
        ]
    },

    # =========================================================================
    # CATEGORIA 3: ANOMALIA DE HARDWARE FUTURO (ZERO-TRUST)
    # Testa se o modelo barra alucinações de hardware que ainda não existe no "Hoje".
    # =========================================================================
    {
        "id": "TC_FUTURE_ANOMALY_01",
        "input": "Should I upgrade my Nitro 5 to the new NVIDIA RTX 6080 GPU?",
        "reference_date": "2026-03-24",
        "expected_output": "[TIMELINE_ANOMALY] The RTX 6080 does not exist as of March 2026. [INTERNAL] NVIDIA's current high-end series is the RTX 50-series. Upgrading laptop GPUs is generally not possible due to BGA soldering.",
        "expected_context": ["[YEAR: 2025] NVIDIA RTX 50-series mobile lineup announcement."]
    },

    # =========================================================================
    # CATEGORIA 4: SKU PRECISION (MISMATCH)
    # Diferenciação cirúrgica entre modelos visualmente idênticos.
    # =========================================================================
    {
        "id": "TC_SKU_MISMATCH_01",
        "input": "Does the AN515-56 have the same Thunderbolt port as the AN515-57?",
        "reference_date": "2025-01-01",
        "expected_output": "[SKU MISMATCH] [RAG] No. The AN515-56 has a standard USB-C 3.2 Gen 2 port, whereas the AN515-57 variant includes Thunderbolt 4 support.",
        "expected_context": [
            "[YEAR: 2021] AN515-56 Specs: 1x USB-C 3.2 Gen 2 (No Thunderbolt).",
            "[YEAR: 2021] AN515-57 Specs: Includes Thunderbolt 4 and HDMI 2.1."
        ]
    },

    # =========================================================================
    # CATEGORIA 5: HÍBRIDO (EXPLICAÇÃO TÉCNICA + DADO RAG)
    # Testa se ele usa o [INTERNAL] apenas para o "Por que" ou "Como".
    # =========================================================================
    {
        "id": "TC_HYBRID_KNOWLEDGE_01",
        "input": "Why is my Nitro 5 reaching 95°C and how can I fix it according to the 2025 guide?",
        "reference_date": "2026-01-01",
        "expected_output": """[RAG] The 2025 Maintenance Guide recommends undervolting and repasting with liquid metal. 
        [INTERNAL] High temperatures in gaming laptops are often caused by dust buildup or dried thermal paste, leading to thermal throttling to protect the CPU. Source: General Hardware Knowledge.""",
        "expected_context": ["[YEAR: 2025] Thermal Optimization Guide: Use undervolting for Nitro 5 series to maintain temps below 85C."]
    }   
]