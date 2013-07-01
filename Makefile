VERSION = $(shell python -c 'import grape; print grape.__version__')
BUNDLE_ENV27 = $(shell pwd)/bundle/env27
BUNDLE_ENV26 = $(shell pwd)/bundle/env26
BUNDLE_DIR = $(shell pwd)/bundle/grape-$(VERSION)
DOWNLOAD_CACHE = downloads
PIP_OPTIONS = --download-cache $(DOWNLOAD_CACHE) --install-option="--prefix=$(BUNDLE_DIR)"

.PHONY: docs docs-clean

all:
	python setup.py build

devel:
	git submodule init
	git submodule update
	cd lib/jip/; python setup.py develop
	python setup.py develop

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

	@echo "Bundeling for 2.7"
	@mkdir -p $(BUNDLE_DIR)/lib/python2.7/site-packages
	@virtualenv -p python2.7 $(BUNDLE_ENV27)
	@. $(BUNDLE_ENV27)/bin/activate; pip install -r bundle_requirements.txt $(PIP_OPTIONS)
	@. $(BUNDLE_ENV27)/bin/activate; pip install lib/jip $(PIP_OPTIONS)
	@. $(BUNDLE_ENV27)/bin/activate; python setup.py install --old-and-unmanageable --prefix=$(BUNDLE_DIR)
	
	@echo "Bundeling for 2.6"
	@mkdir -p $(BUNDLE_DIR)/lib/python2.6/site-packages
	@virtualenv -p python2.6 $(BUNDLE_ENV26)
	@. $(BUNDLE_ENV26)/bin/activate; pip install -r bundle_requirements.txt $(PIP_OPTIONS)
	@. $(BUNDLE_ENV26)/bin/activate; pip install lib/jip $(PIP_OPTIONS)
	@. $(BUNDLE_ENV26)/bin/activate; python setup.py install --old-and-unmanageable --prefix=$(BUNDLE_DIR)

	@rm $(BUNDLE_DIR)/*.rst $(BUNDLE_DIR)/bin/buildout $(BUNDLE_DIR)/bin/mako-render # remove some artifacts created during installation
	@cp dist-utils/grape.py $(BUNDLE_DIR)/bin/grape
	@cp dist-utils/grape-buildout.py $(BUNDLE_DIR)/bin/grape-buildout
	@cp dist-utils/README.txt $(BUNDLE_DIR)/
	@mkdir -p $(BUNDLE_DIR)/conf
	@cp dist-utils/cluster.json	$(BUNDLE_DIR)/conf
	@cp dist-utils/jobs.json $(BUNDLE_DIR)/conf

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
