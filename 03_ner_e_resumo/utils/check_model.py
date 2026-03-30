import requests
import json

def check_ollama_status(model_name="llama3.2:3b"):
    base_url = "http://localhost:11434"
    
    print(f"--- Verificando Ollama para o modelo: {model_name} ---")
    
    try:
        # 1. Verifica se o serviço está online
        version_res = requests.get(f"{base_url}/api/tags")
        if version_res.status_code == 200:
            models = [m['name'] for m in version_res.json().get('models', [])]
            if model_name in models:
                print(f"✅ Modelo '{model_name}' encontrado no sistema.")
            else:
                print(f"❌ Modelo '{model_name}' NÃO encontrado. Disponíveis: {models}")
                return
        
        # 2. Verifica se o modelo está carregado na RAM/VRAM (Running)
        ps_res = requests.get(f"{base_url}/api/ps")
        if ps_res.status_code == 200:
            running_models = ps_res.json().get('models', [])
            if any(model_name in m['name'] for m in running_models):
                print(f"🔥 O modelo '{model_name}' está ATIVO e rodando na GPU/CPU.")
            else:
                print(f"💤 O modelo '{model_name}' está instalado, mas em repouso (ocioso).")
        
        # 3. Teste rápido de inferência
        print("\n--- Testando resposta rápida ---")
        test_res = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model_name,
                "prompt": "Responda apenas 'OK' se estiver funcionando.",
                "stream": False
            }
        )
        if test_res.status_code == 200:
            print(f"🚀 Resposta da IA: {test_res.json().get('response').strip()}")
        else:
            print(f"⚠️ Erro ao gerar resposta: {test_res.status_code}")

    except requests.exceptions.ConnectionError:
        print("🚨 ERRO: O Ollama não está rodando. Abra o Ollama Desktop ou execute 'ollama serve'.")

if __name__ == "__main__":
    # Altere para o modelo que você quer testar (ex: "qwen3:4b-instruct")
    check_ollama_status("llama3.2:3b")