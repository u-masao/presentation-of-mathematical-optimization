import logging
import tempfile
from pathlib import Path

import click
import mlflow
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


def log_artifact_from_message(message, filename):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / filename
        open(file_path, "w").write(message)
        mlflow.log_artifact(file_path)


def generate(input_text, model_name="gpt-4o-2024-08-06", temperature=0.8):
    logger = logging.getLogger(__name__)

    chat = ChatOpenAI(temperature=temperature, model_name=model_name)

    system = ("あなたは優秀なプロンプトエンジニアです。"
    "ユーザーの指示に従って史上最強のプロンプトを作成してください。")
    human = "{text}"
    prompt = ChatPromptTemplate.from_messages(
        [("system", system), ("human", human)]
    )

    chain = prompt | chat

    logger.info(f"chain: {chain}")
    logger.info(f"prompt: {input_text}")
    result = chain.invoke(
        {
            "text": input_text,
        }
    )
    return result


@click.command()
@click.argument("prompt", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
@click.option("--theme_keyword", type=str, default='推薦モデル')
@click.option("--temperature", type=float, default=0.8)
@click.option("--model_name", type=str, default="gpt-4o-2024-08-06")
def main(**kwargs):

    # init logger
    logger = logging.getLogger(__name__)
    mlflow.set_experiment("generate_prompt")
    mlflow.start_run()
    mlflow.log_params({f"args.{k}": v for k, v in kwargs.items()})

    # load prompt template
    prompt_template = open(kwargs["prompt"], "r").read()

    # make prompt
    prompt = prompt_template.format(theme_keyword=kwargs['theme_keyword'])

    # generate
    result = generate(
        prompt,
        temperature=kwargs["temperature"],
        model_name=kwargs["model_name"],
    )

    # split result
    result_dict = result.dict()
    raw_content = result_dict.pop("content")

    # strip triple backquotes
    lines = str(raw_content).strip().split("\n")
    if lines[0] == "```":
        del lines[0]
    if lines[-1] == "```":
        del lines[-1]
    content = "\n".join(lines)

    # save file
    open(kwargs["output_filepath"], "w").write(content)

    # debug output
    logger.info(result_dict)
    logger.info(raw_content)
    logger.info(content)

    # logging
    log_artifact_from_message(prompt, "prompt.txt")
    log_artifact_from_message(str(raw_content), "generated_raw.md")
    log_artifact_from_message(str(content).strip(), "output.md")
    mlflow.log_params(
        {
            "input_tokens": result_dict["usage_metadata"]["input_tokens"],
            "output_tokens": result_dict["usage_metadata"]["output_tokens"],
            "total_tokens": result_dict["usage_metadata"]["total_tokens"],
            "model_name": result_dict["response_metadata"]["model_name"],
            "system_fingerprint": result_dict["response_metadata"][
                "system_fingerprint"
            ],
            "finish_reason": result_dict["response_metadata"]["finish_reason"],
            "id": result_dict["id"],
        }
    )
    mlflow.end_run()


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    load_dotenv()
    main()
