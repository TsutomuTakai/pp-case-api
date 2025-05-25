FROM python:3.12-slim-buster # Alterado para Python 3.12

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo requirements.txt para o contêiner
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação para o contêiner
COPY . .

# Expõe a porta em que a aplicação Flask será executada
EXPOSE 5000

# Define a variável de ambiente para que o Flask saiba onde encontrar a aplicação
ENV FLASK_APP=app.py

# Comando para rodar a aplicação Flask
# Use gunicorn para um ambiente de produção mais robusto
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
