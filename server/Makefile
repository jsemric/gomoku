SHELL := /bin/bash
IMAGE=server
PYTHON_BIN?=python3

build:
	@$(PYTHON_BIN) setup.py build_ext --inplace
	@mv utils.cpython* gomoku/

start:
	PYTHONPATH=gomoku LOG_LEVEL=DEBUG $(PYTHON_BIN) -m uvicorn --host 0.0.0.0 --port 3001 --factory "gomoku.app:create_app" --reload

fmt:
	@$(PYTHON_BIN) -m black gomoku tests

test: build
	@$(PYTHON_BIN) -m coverage run --source gomoku --omit gomoku/setup.py -m pytest -o log_cli=false --doctest-modules
	@$(PYTHON_BIN) -m coverage report
	@$(PYTHON_BIN) -m coverage html

clean:
	@rm -rf tests/.pytest_cache .pytest_cache gomoku/build gomoku/*.so gomoku/*.c htmlcov .coverage build
