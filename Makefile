CLIENT_DIR=client
SERVER_DIR=server

.PHONY: run-server
start-server:
	@cd $(SERVER_DIR) && $(MAKE) start

.PHONY: run-client
start-client:
	@cd $(CLIENT_DIR) && yarn start

.PHONY: start
start: stop
	@docker compose up --build --remove-orphans -d
	@firefox http://localhost:80

.PHONY: stop
stop:
	@docker compose down --remove-orphans
