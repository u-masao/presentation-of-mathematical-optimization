

##### generate slide #####
## generate slide
all: lint repro

## run generate slide pipeline
repro: check_commit PIPELINE.md
	poetry run dvc repro -f
	git commit dvc.lock -m 'dvc repro' || true

## commit check
check_commit:
	git diff --exit-code
	git diff --exit-code --staged

## make pipeline file
PIPELINE.md: dvc.yaml params.yaml
	poetry run dvc dag --md > $@
	git commit $@ -m 'update dvc pipeline' || true


##### setup #####
## setup
setup: poetry_install build_image

## install poetry environment
poetry_install:
	poetry install

# build docker image for marp-cli japanese
build_image:
	docker build -t marp-cli-ja .


##### utils #####
## linter & formatter
lint:
	poetry run isort src
	poetry run black src -l 79
	poetry run flake8 src
	poetry run mdformat src/prompt.md

## mlflow ui runner
mlflow_ui:
	poetry run mlflow ui

## list installed font on marp container
list_fonts:
	docker run -it --entrypoint fc-list  marp-cli-ja | sort
