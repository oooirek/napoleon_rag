.PHONY: start stop restart logs

ROOT_DIR := $(shell pwd)
RUN_DIR  := $(ROOT_DIR)/.run
LOG_DIR  := $(ROOT_DIR)/logs

OLLAMA_PID := $(RUN_DIR)/ollama.pid
BOT_PID    := $(RUN_DIR)/bot.pid

start:
	@mkdir -p $(RUN_DIR) $(LOG_DIR)
	@echo "[start] docker compose up -d"
	@docker compose up -d
	@if pgrep -f "ollama serve" >/dev/null 2>&1; then \
		echo "[start] ollama serve already running"; \
	else \
		echo "[start] ollama serve"; \
		nohup ollama serve > $(LOG_DIR)/ollama.log 2>&1 & echo $$! > $(OLLAMA_PID); \
	fi
	@if [ -f $(BOT_PID) ] && kill -0 $$(cat $(BOT_PID)) 2>/dev/null; then \
		echo "[start] bot already running"; \
	else \
		echo "[start] python -m src.main"; \
		nohup poetry run python -m src.main > $(LOG_DIR)/bot.log 2>&1 & echo $$! > $(BOT_PID); \
	fi
	@echo "[start] done"

stop:
	@if [ -f $(BOT_PID) ]; then \
		PID=$$(cat $(BOT_PID)); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "[stop] stopping bot ($$PID)"; \
			kill $$PID 2>/dev/null || true; \
			sleep 1; \
			kill -0 $$PID 2>/dev/null && kill -9 $$PID 2>/dev/null || true; \
		fi; \
		rm -f $(BOT_PID); \
	fi
	@if [ -f $(OLLAMA_PID) ]; then \
		PID=$$(cat $(OLLAMA_PID)); \
		if kill -0 $$PID 2>/dev/null; then \
			echo "[stop] stopping ollama ($$PID)"; \
			kill $$PID 2>/dev/null || true; \
			sleep 1; \
			kill -0 $$PID 2>/dev/null && kill -9 $$PID 2>/dev/null || true; \
		fi; \
		rm -f $(OLLAMA_PID); \
	elif pgrep -f "ollama serve" >/dev/null 2>&1; then \
		echo "[stop] stopping ollama (pgrep)"; \
		pkill -f "ollama serve" || true; \
	fi
	@echo "[stop] docker compose stop"
	@docker compose stop
	@echo "[stop] done"

restart: stop start

logs:
	@tail -f $(LOG_DIR)/bot.log