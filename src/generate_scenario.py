import logging

import click
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


def generate(input_text, model_name="gpt-4o-2024-08-06"):
    logger = logging.getLogger(__name__)

    chat = ChatOpenAI(temperature=0, model_name=model_name)

    system = "あなたは有能なアシスタントです。ユーザーの指示に基づいて最も適切な回答をしてください。"
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
def main(**kwargs):

    # init logger
    logger = logging.getLogger(__name__)

    # load prompt
    prompt = open(kwargs["prompt"], "r").read()

    # generate
    result = generate(prompt)

    # debug output
    logger.debug(result.dict())
    logger.info(result.content)

    # save
    open(kwargs["output_filepath"], "w").write(str(result.content).strip())


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    load_dotenv()
    main()
