NAME := $(shell basename $(PWD))
PYTHONPATH := $(PWD)/.
VENV := $(PWD)/.venv

PATH := $(VENV)/bin:$(PATH)
BIN := PATH=$(PATH) PYTHONPATH=$(PYTHONPATH) $(VENV)/bin
py := $(BIN)/python3
pip := $(py) -m pip

.PHONY: test
test:
	$(BIN)/pytest tests

.PHONY: lint
lint:
	$(BIN)/ruff check $(NAME) tests

.PHONY: black
black:
	$(BIN)/black $(NAME) tests

.PHONY: bump
bump:
	$(eval TMP := $(shell mktemp tmp.pyproject.XXXXXX))
	@awk '$$1=="version"{gsub("\"","",$$3);split($$3,n,".");$$3=sprintf("\"%d.%d.%d\"",n[1],n[2],n[3]+1)}{print}' pyproject.toml > $(TMP)
	@mv $(TMP) pyproject.toml
	@grep ^version\ = pyproject.toml

.PHONY: bin
bin:
	@echo $(BIN)

.PHONY: venv
venv:
	python3 -m venv $(VENV)
	$(pip) install --upgrade pip
	$(pip) install -r requirements.dev
