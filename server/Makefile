SHELL := /bin/bash
IMAGE=server
PYTHON_BIN?=python3

build:
	@cd src && $(PYTHON_BIN) setup.py build_ext --inplace

start:
	PYTHONPATH=src LOG_LEVEL=DEBUG $(PYTHON_BIN) -m uvicorn --host 0.0.0.0 --port 3001 --factory "src.app:create_app" --reload

fmt:
	@$(PYTHON_BIN) -m black src tests

test: build
	@$(PYTHON_BIN) -m coverage run --source src --omit src/setup.py -m pytest -o log_cli=false --doctest-modules
	@$(PYTHON_BIN) -m coverage report
	@$(PYTHON_BIN) -m coverage html

clean:
	@rm -fr tests/.pytest_cache .pytest_cache src/build src/*.so src/*.c htmlcov .coverage
