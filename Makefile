.PHONY: test test-build test-run test-clean help

help:
	@echo "Available targets:"
	@echo "  test        - Build and run all tests"
	@echo "  test-build  - Build test container"
	@echo "  test-run    - Run tests (requires built container)"
	@echo "  test-clean  - Clean test containers and volumes"

test: test-build test-run

test-build:
	docker-compose -f dev/docker-compose.test.yml build

test-run:
	docker-compose -f dev/docker-compose.test.yml up --abort-on-container-exit

test-clean:
	docker-compose -f dev/docker-compose.test.yml down -v
	docker-compose -f dev/docker-compose.test.yml rm -f
