# Makefile
#
# Este Makefile automatiza tarefas comuns do projeto Flask.
# Para usuários Windows: Recomenda-se executar este Makefile usando Git Bash ou WSL (Windows Subsystem for Linux).

.PHONY: build-dev build-prod test build-docker run clean all install-podman-deps create-venv

# --- Variáveis de Configuração ---
# Caminho para o diretório do ambiente virtual
# !!! AJUSTE ESTA LINHA SE O NOME DO SEU DIRETÓRIO VIRTUAL FOR DIFERENTE (ex: venv-unix) !!!
VENV_DIR = venv

# Comandos Python e Pip dentro do ambiente virtual
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
FLASK = $(VENV_DIR)/bin/flask
PYTEST = $(VENV_DIR)/bin/pytest

# Comando podman-compose. Será verificado e instalado se necessário.
PODMAN_COMPOSE_CMD = $(VENV_DIR)/bin/podman-compose

# Nome da imagem Docker/Podman
DOCKER_IMAGE_NAME = flask-user-crud-advanced

# --- Alvos do Makefile ---

# Alvo auxiliar: create-venv
# Garante que o ambiente virtual seja criado e o pip interno seja atualizado.
create-venv:
	@echo "--- Verificando e criando ambiente virtual ---"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Criando ambiente virtual..."; \
		python3 -m venv $(VENV_DIR); \
		echo "Ambiente virtual criado."; \
	else \
		echo "Ambiente virtual já existe."; \
	fi
	@echo "Atualizando pip, setuptools e wheel no ambiente virtual..."
	# Usa o python recém-criado para atualizar o pip, setuptools e wheel
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	@echo "Ambiente virtual pronto."


# Alvo: build-dev
# Configura o ambiente de desenvolvimento local: cria o venv, instala dependências (incluindo podman-compose)
# e aplica migrações do DB.
build-dev: create-venv install-podman-deps
	@echo "--- Construindo ambiente de desenvolvimento ---"
	@echo "Ativando ambiente virtual e instalando dependências do projeto..."
	$(PIP) install -r requirements.txt
	@echo "Aplicando migrações do banco de dados..."
	$(FLASK) db update
	@echo "Ambiente de desenvolvimento configurado com sucesso!"

# Alvo: install-podman-deps
# Garante que o podman-compose esteja instalado no ambiente virtual.
install-podman-deps: create-venv # Garante que o venv exista antes de tentar instalar o podman-compose
	@echo "--- Verificando e instalando dependências do Podman (podman-compose) ---"
	@if ! $(PYTHON) -c "import importlib.util; import sys; sys.exit(0 if importlib.util.find_spec('podman_compose') else 1)"; then \
		echo "Instalando podman-compose no ambiente virtual..."; \
		$(PIP) install podman-compose; \
	else \
		echo "podman-compose já está instalado no ambiente virtual."; \
	fi
	@echo "Dependências do Podman verificadas."

# Alvo: build-prod
# Constrói a imagem Docker/Podman para produção usando o podman-compose.
build-prod: create-venv install-podman-deps # Garante que o venv e podman-compose existam para este alvo
	@echo "--- Construindo imagem de produção (via Podman Compose) ---"
	$(PODMAN_COMPOSE_CMD) build web --no-cache
	@echo "Imagem de produção 'web' construída com sucesso via Podman Compose."

# Alvo: test
# Executa todos os testes do projeto usando pytest.
# Assume que pytest.ini está configurado na raiz para encontrar os testes.
test: create-venv
	@echo "--- Executando testes ---"
	$(PYTEST) -s # Adicionei -s para ver logs das fixtures
	@echo "Testes concluídos."

# Alvo: build-docker
# Constrói a imagem Docker/Podman diretamente, sem usar o compose.
build-docker:
	@echo "--- Construindo imagem Docker/Podman diretamente ---"
	podman build -t $(DOCKER_IMAGE_NAME):latest .
	@echo "Imagem Docker/Podman '$(DOCKER_IMAGE_NAME):latest' construída com sucesso."

# Alvo: run
# Inicia a aplicação em modo de desenvolvimento via Podman Compose (em background).
run: create-venv install-podman-deps # Garante que o venv e podman-compose existam para este alvo
	@echo "--- Iniciando aplicação (via Podman Compose) ---"
	$(PODMAN_COMPOSE_CMD) up -d
	@echo "Aplicação iniciada em segundo plano. Acesse em http://localhost:5000"
	@echo "Para ver os logs: $(PODMAN_COMPOSE_CMD) logs -f"
	@echo "Para parar a aplicação: $(PODMAN_COMPOSE_CMD) down"

# Alvo: clean
# Limpa arquivos gerados pelo projeto (venv, banco de dados, logs, caches, etc.).
clean:
	@echo "--- Limpando arquivos do projeto ---"
	# Remove o diretório do ambiente virtual
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Removendo ambiente virtual..."; \
		rm -rf $(VENV_DIR); \
	fi
	# Remove o banco de dados SQLite e logs
	@if [ -d "instance" ]; then \
		echo "Removendo arquivos de banco de dados..."; \
		rm -f instance/*.db; \
	fi
	@if [ -d "logs" ]; then \
		echo "Removendo arquivos de log..."; \
		rm -f logs/*.log; \
	fi
	# Remove caches do pytest e Python
	@echo "Removendo caches..."
	rm -rf .pytest_cache
	find . -name "__pycache__" -exec rm -rf {} +
	@echo "Limpeza concluída."

# Alvo padrão: executa build-dev, test e run
all: build-dev test run