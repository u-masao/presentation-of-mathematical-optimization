
lint:
	poetry run isort src
	poetry run black src -l 79
	poetry run flake8 src

repro:
	poetry run dvc repro -f
