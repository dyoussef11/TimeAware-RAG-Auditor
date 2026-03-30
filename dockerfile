FROM python:3.11-slim

# Diretório de trabalho no container
WORKDIR /app

# Copiar dependências
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código
COPY . .

# Comando padrão (pode rodar um script direto)
CMD ["python", "main.py"]
    