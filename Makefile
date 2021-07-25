.PHONY: install-hooks clean-build docs view-docs
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

# Print the comment for each make command
for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

install-hooks: ## Install and run pre-commit hooks
	pre-commit install
	pre-commit run --all-files

clean-build: ## Remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

docs: ## Generate Sphinx HTML documentation
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

view-docs: ## Open Sphinx HTML documentation in a browser
	python -m webbrowser -t docs/_build/html/index.html

install: ## Install the package
	python setup.py install

install-dev: ## Install development version
	pip install -e .[dev]
