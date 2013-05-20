all:
	python setup.py build

devel:
	cd lib/another_tool/; python setup.py develop
	python setup.py develop

test:
	@echo -n "Running pytest"
	@py.test -q tests
	@echo "All tests ran successfully";fi
