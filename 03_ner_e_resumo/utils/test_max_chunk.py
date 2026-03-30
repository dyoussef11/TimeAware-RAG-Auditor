import asyncio
import time
from openai import AsyncOpenAI
from pynvml import *

# Configuração do Cliente
client = AsyncOpenAI(base_url='http://localhost:11434/v1', api_key='ollama', timeout=300.0)
MODELO = "llama3.2:3b"

async def test_chunk_capacity(num_comments):
    # Simula um comentário técnico médio (~200 palavras / 1000 chars)
    fake_comment = "The laptop screen flickers when the hinge is moved. Possible cable issue. " * 15
    contexto_fake = "".join([f"COMMENT {i}: {fake_comment}\n" for i in range(num_comments)])
    
    print(f"\n🧪 Testando Chunk com {num_comments} comentários...")
    print(f"📏 Tamanho estimado do texto: {len(contexto_fake)} caracteres")

    start_time = time.time()
    try:
        nvmlInit()
        handle = nvmlDeviceGetHandleByIndex(0)
        
        response = await client.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Extract technical facts as JSON."},
                {"role": "user", "content": contexto_fake}
            ],
            response_format={"type": "json_object"},
            extra_body={"options": {"num_ctx": 8192, "temperature": 0.0}}
        )
        
        duration = time.time() - start_time
        info = nvmlDeviceGetMemoryInfo(handle)
        vram_used = info.used / 1024**2
        
        print(f"✅ SUCESSO: Processado em {duration:.2f}s")
        print(f"🧠 Consumo de VRAM: {vram_used:.0f}MB / 4096MB")
        return True, duration
    
    except Exception as e:
        print(f"❌ FALHA: {str(e)}")
        return False, 0

async def main():
    # Testa de 10 em 10 até o limite
    tamanhos_para_testar = [10, 20, 30, 40, 50, 60, 80, 100]
    resultados = []

    for n in tamanhos_para_testar:
        sucesso, tempo = await test_chunk_capacity(n)
        if not sucesso:
            print(f"\n🚫 LIMITE ATINGIDO! O sistema aguentou até perto de {n-10} comentários por chunk.")
            break
        resultados.append((n, tempo))
        await asyncio.sleep(5) # Cooldown entre testes

    print("\n--- RESUMO DO TESTE ---")
    for n, t in resultados:
        print(f"Comentários: {n} | Tempo: {t:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())