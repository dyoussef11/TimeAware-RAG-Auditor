# 1. WHITE LIST EXaustiva (Foco: Problema, Solução, Upgrade, Guia)
# Baseado no flair_reddit.txt - Mantém mesmo com emojis ou nomes repetidos
FLAIRS_TECNICOS_KEEP = [
    # Status de Resolução
    'problem solved', 'solved', 'resolved', 'answered', 'fixed', 'solution',
    '✅️ problem solved', '✅️ solved', '✅ solved', 'solved!', 'problem solved ✅',
    
    # Suporte e Ajuda (Variantes exatas e raízes)
    'help', 'support', 'technical help', 'tech support', 'need help', 'help request',
    'question', 'doubt', 'query', 'assistance', 'troubleshooting', 'diagnostic',
    '💻 help', '🔧 tech support', '⚠️ problem', '❓ question', '❕ help', 
    'help ساعدني', 'ajuda / help', 'question سؤال', 'build - help',
    
    # Códigos de Sistema e Ícones
    ':bug:', ':help:', ':support:', ':hardware:', ':settings:', ':symbolwarning:',
    'bug', 'bugs', 'glitch', 'error', 'crash', 'bsod', 'blue screen', 'technical issue',
    'hardware issue', 'software issue', 'system failure', 'unresolved', 'unsolved',
    
    # Upgrades e Hardware (Ouro para o RAG)
    'upgrade', 'build upgrade', 'replacement', 'install', 'hardware', 'laptop add-ons',
    'peripherals', 'gpu', 'cpu', 'ram', 'ssd', 'nvme', 'sata', 'psu', 'motherboard',
    'display', 'monitor', 'screen', 'thermal', 'repaste', 'cooling', 'fan', 'battery',
    'maintenance', '🛠 laptop add-ons', 'upgrade questions', 'new user setup',
    
    # Conhecimento, Dicas e Testes
    'guide', 'tutorial', 'how-to', 'tips', 'tricks', 'useful info', 'information',
    'technical discussion', 'tech discussion', 'insight', '⭐ guide list', 
    '📋 guide list', '💡 tips', 'flash: tips & guides', 'user reviews', 
    'official review', 'detailed build log', 'benchmark', 'performance', 'fps',
    'stress test', 'overclocking', 'undervolting', 'xtu', 'throttling', 'latency',
    '📈 benchmark results', 'benchmark score'
]

# 2. BLACK LIST: Ruído comercial, social e estético (A ser removido)
FLAIRS_RUIDO_DROP = [
    'sale', 'deal', 'deals', 'buying', 'purchase', 'price', 'market', 'shop', 'store',
    'wts', 'wtb', 'selling', 'sold', 'giveaway', 'black friday', 'cyber monday',
    'prime day', 'meme', 'funny', 'fluff', 'rant', 'shitpost', 'nostalgia', 'off-topic',
    'photo', 'picture', 'setup', 'battlestation', 'showoff', 'joined the club',
    'it\'s here', 'just arrived', 'unboxing', 'shipping', 'delivery', 'announcement',
    'news', 'megathread', 'mod post', 'official mod post', 'weekly', 'meta', 
    'video', 'vidéo', 'youtube', 'battlestation pictures', 'megathread', 'purchase advice', 'build questions', 'daily thread', 'weekly thread'
]