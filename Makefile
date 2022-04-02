CLIENT_DIR=client
SERVER_DIR=server

.PHONY: run-server
start-server:
	@cd $(SERVER_DIR) && $(MAKE) start

.PHONY: run-client
start-client:
	@cd $(CLIENT_DIR) && yarn start

.PHONY: fmt
fmt:
	@black $(SERVER_DIR)
	@cd $(CLIENT_DIR) && yarn fmt

.PHONY: test
test:
	@cd $(SERVER_DIR) && $(MAKE) test
