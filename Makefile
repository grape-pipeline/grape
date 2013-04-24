all:
	python setup.py build

devel:
	cd lib/another_tool/; python setup.py develop
	python setup.py develop
