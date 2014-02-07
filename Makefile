VERSION = $(shell python -c 'import grape; print grape.__version__')
BUNDLE_ENV27 = $(shell pwd)/bundle/env27
BUNDLE_ENV26 = $(shell pwd)/bundle/env26
BUNDLE_DIR = $(shell pwd)/bundle/grape-$(VERSION)
DOWNLOAD_CACHE = downloads
PIP_OPTIONS = --download-cache $(DOWNLOAD_CACHE)
DEVEL_ENV = $(shell pwd)
INSTALL_DIR = $(shell pwd)
INSTALL_LOG = $(shell pwd)/install.log

.PHONY: docs docs-clean

all:
	python setup.py build

devel:
	@if [ ! -d $(DEVEL_ENV) ]; then virtualenv --no-site-packages $(DEVEL_ENV);fi
	@. $(DEVEL_ENV)/bin/activate;pip install -r requirements.txt $(PIP_OPTIONS)
	@. $(DEVEL_ENV)/bin/activate;python setup.py develop
	@echo "Development setup completed."
	@echo ""
	@echo "------------------------------------------------------"
	@echo "Please remember that each time you want to use Grape 2"
	@echo "you will have to run the folowing command:"
	@echo ""
	@echo ". bin/activate"
	@echo "------------------------------------------------------"

install:
	@if [ ! -d $(INSTALL_DIR) ]; then virtualenv --no-site-packages $(INSTALL_DIR);fi
	@echo "Installing Grape 2 into $(INSTALL_DIR)..."
	@. $(INSTALL_DIR)/bin/activate;pip install -r install_requirements.txt $(PIP_OPTIONS) > $(INSTALL_LOG) 2>&1
	@. $(INSTALL_DIR)/bin/activate;python setup.py install > $(INSTALL_LOG) 2>&1
	@echo "Install completed."
	@echo ""
	@echo "------------------------------------------------------"
	@echo "Please remember that each time you want to use Grape 2"
	@echo "you will have to run the folowing command:"
	@echo ""
	@echo ". bin/activate"
	@echo "------------------------------------------------------"

test:
	@echo -n "Running pytest"
	@py.test -q tests
	@echo "All tests ran successfully"

bundle: downloads
	@echo "Creating bundled distribution for $(VERSION)"
	@rm -rf $(BUNDLE_ENV27)

	@rm -rf $(BUNDLE_DIR)
	@rm -f bundle/grape-$(VERSION)
	@rm -rf $(BUNDLE_ENV27)
	@rm -rf $(BUNDLE_ENV26)

ifneq ($(shell which python2.7),) 
	@echo "Bundeling for 2.7"
	@mkdir -p $(BUNDLE_DIR)/lib/python2.7/site-packages
	@virtualenv -p python2.7 $(BUNDLE_ENV27)
	@. $(BUNDLE_ENV27)/bin/activate; pip install -r install_requirements.txt $(PIP_OPTIONS)
	@. $(BUNDLE_ENV27)/bin/activate; python setup.py install 
	@cp -R $(BUNDLE_ENV27)/lib/python2.7/site-packages/* $(BUNDLE_DIR)/lib/python2.7/site-packages
endif
	
ifneq ($(shell which python2.6),)
	@echo "Bundeling for 2.6"
	@mkdir -p $(BUNDLE_DIR)/lib/python2.6/site-packages
	@virtualenv -p python2.6 $(BUNDLE_ENV26)
	@. $(BUNDLE_ENV26)/bin/activate; pip install -r install_requirements.txt $(PIP_OPTIONS)
	@. $(BUNDLE_ENV26)/bin/activate; python setup.py install
	@cp -R $(BUNDLE_ENV26)/lib/python2.6/site-packages/* $(BUNDLE_DIR)/lib/python2.6/site-packages
endif


	@mkdir -p $(BUNDLE_DIR)/bin
	@cp dist-utils/grape.py $(BUNDLE_DIR)/bin/grape
	@cp dist-utils/grape-buildout.py $(BUNDLE_DIR)/bin/grape-buildout
	@cp dist-utils/README.txt $(BUNDLE_DIR)/
	@mkdir -p $(BUNDLE_DIR)/conf

	@tar -C bundle -czf bundle/grape-$(VERSION).tar.gz grape-$(VERSION)

docs:
	@test -d ./docs && cd docs; $(MAKE) html

docs-clean:
	@test -d docs && cd docs; $(MAKE) clean

downloads:
	@mkdir -p $(DOWNLOAD_CACHE)

clean:
	@rm -rf bundle/
	@rm -rf build/
	@rm -rf dist/
