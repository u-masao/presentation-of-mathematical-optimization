import logging
import tempfile
from pathlib import Path

import click
import markdown_to_json
import mlflow
from dotenv import load_dotenv
from pptx import Presentation


def log_artifact_from_message(message, filename):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / filename
        open(file_path, "w").write(message)
        mlflow.log_artifact(file_path)


def make_presentation(docs):
    prs = Presentation()
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]
    title.text = "Hello, World!"
    subtitle.text = "python-pptx was here!"
    return prs


def convert_markdown_to_pptx(md_text):
    docs = markdown_to_json.dictify(md_text)
    return make_presentation(docs)


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
def main(**kwargs):

    # init logger
    logger = logging.getLogger(__name__)
    logger.info(f"args: {kwargs}")
    mlflow.set_experiment("make_pptx")
    mlflow.start_run()
    mlflow.log_params({f"args.{k}": v for k, v in kwargs.items()})

    # load prompt
    md_text = open(kwargs["input_filepath"], "r").read()

    # convert
    presentation = convert_markdown_to_pptx(
        md_text,
    )

    # save file
    presentation.save(kwargs["output_filepath"])

    # logging
    mlflow.log_artifact(kwargs["output_filepath"])
    mlflow.end_run()


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    load_dotenv()
    main()
