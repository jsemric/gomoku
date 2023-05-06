IMAGE=server

start:
	PYTHONPATH=src LOG_LEVEL=DEBUG python -m uvicorn --factory "src.app:setup_app" --reload

test:# build_ext
	@coverage run --source src --omit src/setup.py -m pytest -o log_cli=false --doctest-modules
	@coverage report
	@coverage html

build_ext:
	@cd src && python setup.py build_ext --inplace

clean:
	@rm -fr tests/.pytest_cache .pytest_cache src/build src/*.so src/*.c htmlcov .coverage