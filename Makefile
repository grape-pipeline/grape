VERSION = $(shell python -c 'import grape; print grape.__version__')
BUNDLE_ENV27 = $(shell pwd)/bundle/env27
BUNDLE_DIR = $(shell pwd)/bundle/grape-$(VERSION)

all:
	python setup.py build

devel:
	cd lib/another_tool/; python setup.py develop
	python setup.py develop

test:
	@echo -n "Running pytest"
	@py.test -q tests
	@echo "All tests ran successfully"

bundle:
	@echo "Creating bundled distribution for $(VERSION)"
	@rm -rf $(BUNDLE_ENV27)
	# create dist for python 2.7
	@virtualenv -p python2.7 $(BUNDLE_ENV27)
	@rm -rf $(BUNDLE_DIR)
	@mkdir -p $(BUNDLE_DIR)/lib/python2.7/site-packages
	. $(BUNDLE_ENV27)/bin/activate; pip install -r bundle_requirements.txt --install-option="--prefix=$(BUNDLE_DIR)"
	. $(BUNDLE_ENV27)/bin/activate; pip install lib/jip --install-option="--prefix=$(BUNDLE_DIR)"
	. $(BUNDLE_ENV27)/bin/activate; python setup.py install --old-and-unmanageable --prefix=$(BUNDLE_DIR)
	@rm $(BUNDLE_DIR)/*.rst $(BUNDLE_DIR)/bin/buildout $(BUNDLE_DIR)/bin/mako-render # remove some artifacts created during installation
	@cp dist-utils/grape.py $(BUNDLE_DIR)/bin/grape
	@cp dist-utils/grape-buildout.py $(BUNDLE_DIR)/bin/grape-buildout
clean:
	@rm -rf bundle/
	@rm -rf build/
	@rm -rf dist/
