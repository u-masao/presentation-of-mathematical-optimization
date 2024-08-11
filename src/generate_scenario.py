import os

import click
from dotenv import load_dotenv


def generate(prompt, api_key):
    return "result text"


@click.command()
@click.argument("prompt", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
def main(**kwargs):

    openai_api_key = os.environ["OPENAI_API_KEY"]

    prompt = open(kwargs["prompt"], "r")

    result = generate(prompt, openai_api_key)

    print(result)

    open(kwargs["output_filepath"], "w").write(result)


if __name__ == "__main__":
    load_dotenv()
    main()
