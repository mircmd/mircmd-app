.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: init
init: ## Install dependencies
	@cargo install cargo-component --locked
	@cargo install tauri-cli --locked
	@npm install

.PHONY: run
run: ## Run the application
	@cargo tauri dev

.PHONY: build
build: ## Build the application
	@cargo tauri build
