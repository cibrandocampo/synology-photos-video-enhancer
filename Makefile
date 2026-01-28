.PHONY: test test-build test-run test-clean dev debug help

help:
	@echo "Available targets:"
	@echo "  test        - Build and run all tests"
	@echo "  test-build  - Build test container"
	@echo "  test-run    - Run tests (requires built container)"
	@echo "  test-clean  - Clean test containers and volumes"
	@echo "  dev         - Run in development mode (hot reload)"
	@echo "  debug       - Run in debug mode (with breakpoints)"

test: test-build test-run

test-build:
	docker compose -f dev/docker compose.test.yml build

test-run:
	docker compose -f dev/docker compose.test.yml up --abort-on-container-exit

test-clean:
	docker compose -f dev/docker compose.test.yml down -v
	docker compose -f dev/docker compose.test.yml rm -f

dev:
	cd dev && docker compose -f docker compose.dev.yml up --build

debug:
	cd dev && docker compose -f docker compose.debug.yml up --build
