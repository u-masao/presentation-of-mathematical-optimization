
all: lint repro
lint:
	poetry run isort src
	poetry run black src -l 79
	poetry run flake8 src

repro: check_commit
	poetry run dvc repro -f
	git commit dvc.lock -m 'dvc repro' || true

check_commit:
	git diff --exit-code
	git diff --exit-code --staged

list_fonts:
	docker run -it --entrypoint fc-list  marp-cli-ja | sort

build_image:
	docker build -t marp-cli-ja .
