import io
import logging
import re
import tempfile
from pathlib import Path

import click
import mlflow
import requests
from dotenv import load_dotenv
from object_cache import object_cache
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm


def log_artifact_from_message(message, filename, mode: str = "w"):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / filename
        open(file_path, mode).write(message)
        mlflow.log_artifact(file_path)


def get_image_as_bytes(url):
    """
    画像をダウンロードして Bytes として返す
    """

    # init logger
    logger = logging.getLogger(__name__)
    logger.debug(f"getting url: {url}")

    # http get request
    response = requests.get(url)
    response.raise_for_status()
    logger.debug(f"content response: {response}")
    logger.debug(f"content length: {len(response.content)}")

    # return Bytes image content
    return response.content


def generate_dummy_image(
    prompt: str,
    model_name: str = "dall-e-3",
    image_width: int = 1024,
    image_height: int = 1024,
    quality: str = "standard",
    n: int = 1,
):
    img = Image.new("RGB", (image_width, image_height), color="green")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default().font_variant(size=100)
    draw.text(
        (image_width // 10, image_height // 10),
        "Dummy Image",
        font=font,
        fill="blue",
    )

    image_bytes = io.BytesIO()
    img.save(image_bytes, format="PNG")
    return [image_bytes.getvalue()]


@object_cache
def generate_image(
    prompt: str,
    model_name: str = "dall-e-3",
    image_width: int = 1024,
    image_height: int = 1024,
    quality: str = "standard",
    n: int = 1,
):
    # 画像を生成
    client = OpenAI()
    response = client.images.generate(
        model=model_name,
        prompt=prompt,
        size=f"{image_width}x{image_height}",
        quality=quality,
        n=n,
    )

    # 画像データを取得してリストを返す
    images = [get_image_as_bytes(x.url) for x in response.data]
    return images


def parse_input_and_generate_image(
    input_text,
    images_dir: str,
    output_filepath: str,
    model_name: str = "dall-e-3",
    enable_dummy: bool = False,
):
    """
    入力をパースして画像を作成
    """
    # init logger
    logger = logging.getLogger(__name__)

    # 変数を初期化
    results = []
    images_dir = Path(images_dir)
    search_regex = r'!\[(.*)\]\((.*) (".*")\)'

    # 入力を行で分解して各行でループ
    lines = input_text.split("\n")
    image_count = 0
    for line in lines:
        # 正規表現で検索
        if re.search(search_regex, line):
            image_count += 0

    with tqdm(total=image_count) as pbar:
        # 各行をチェック
        for index, line in enumerate(lines):

            # 正規表現で検索
            m = re.search(search_regex, line)

            # ヒットした？
            if m is None:
                # ヒットしない場合
                results.append(line)
                continue

            # ヒットした場合
            prompt = m.group(1)
            logger.info(f"{prompt=}")

            # generate
            if enable_dummy:
                images = generate_dummy_image(prompt)
            else:
                images = generate_image(prompt, model_name=model_name)

            # パスを計算
            image_filepath = images_dir / f"image_{index}.png"
            relative_image_path = image_filepath.relative_to(
                Path(output_filepath).parent
            )
            logger.debug(f"{relative_image_path=}")

            # ファイルに出力
            open(image_filepath, "wb").write(images[0])
            mlflow.log_artifact(image_filepath)
            log_artifact_from_message(prompt, f"image_{index}_prompt.txt")

            # 行を編集
            new_lines = (
                f"![width:300px bg right:30%]({relative_image_path})"
                "\n"
                f"<!-- image_prompt: {prompt} -->"
            )

            # 結果に保存
            results.append(new_lines)

            # プログレスバーをアプデート
            pbar.update(1)

    return "\n".join(results)


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True))
@click.argument("output_filepath", type=click.Path())
@click.argument("output_images_dir", type=click.Path())
@click.option("--temperature", type=float, default=0.8)
@click.option("--model_name", type=str, default="dall-e-3")
@click.option("--enable_dummy", type=bool, default=False)
def main(**kwargs):

    # init logger
    logger = logging.getLogger(__name__)
    mlflow.set_experiment("generate")
    mlflow.start_run()
    mlflow.log_params({f"args.{k}": v for k, v in kwargs.items()})
    logger.info(f"args: {kwargs}")

    # 出力ディレクトリを作成
    Path(kwargs["output_images_dir"]).mkdir(parents=True, exist_ok=True)

    # load input markdown
    input_text = open(kwargs["input_filepath"], "r").read()

    # generate
    result = parse_input_and_generate_image(
        input_text,
        model_name=kwargs["model_name"],
        images_dir=kwargs["output_images_dir"],
        output_filepath=kwargs["output_filepath"],
        enable_dummy=kwargs["enable_dummy"],
    )

    # save file
    open(kwargs["output_filepath"], "w").write(result)

    # logging
    log_artifact_from_message(input_text, "input_text.md")
    log_artifact_from_message(result, "output.md")
    mlflow.log_params({})
    mlflow.end_run()


if __name__ == "__main__":
    log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_fmt)
    load_dotenv()
    main()
