import logging
import tempfile
from pathlib import Path

import click
import markdown
import mlflow
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pptx import Presentation
from pptx.util import Mm, Pt

SLIDE_WIDTH_MM = 338.67
SLIDE_HEIGHT_MM = 190.5


def log_artifact_from_message(message, filename):
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / filename
        open(file_path, "w").write(message)
        mlflow.log_artifact(file_path)


def get_layout_by_name(prs, query):
    logger = logging.getLogger(__name__)
    names = [x.name for x in prs.slide_layouts]
    logger.info(f"layout names: {names}")
    index = names.index(query)
    layout = prs.slide_layouts[index]
    logger.info(f"placeholders: {len(layout.placeholders)}")
    logger.info(f"placeholders name: {[x.name for x in layout.placeholders]}")
    return layout


def set_position(placeholder, left=None, top=None, height=None, width=None):
    if left:
        placeholder.left = Mm(left)
    if top:
        placeholder.top = Mm(top)
    if height:
        placeholder.height = Mm(height)
    if width:
        placeholder.width = Mm(width)


def configure_presentation(prs):

    logger = logging.getLogger(__name__)
    slide_master = prs.slide_master
    logger.info(f"slide master layouts: {len(slide_master.slide_layouts)}")

    # プレゼンテーションのサイズを変更
    prs.slide_width = Mm(SLIDE_WIDTH_MM)
    prs.slide_height = Mm(SLIDE_HEIGHT_MM)

    # レイアウト調整(コンテンツ)
    content_layout = get_layout_by_name(prs, "Title and Content")
    set_position(
        content_layout.placeholders[0], 20, 20, 30, SLIDE_WIDTH_MM - 2 * 20
    )
    set_position(
        content_layout.placeholders[1],
        20,
        60,
        SLIDE_HEIGHT_MM - 80,
        SLIDE_WIDTH_MM - 2 * 20,
    )

    # レイアウト調整(タイトルスライド)
    title_layout = get_layout_by_name(prs, "Title Slide")
    set_position(
        title_layout.placeholders[0], 20, 20, 30, SLIDE_WIDTH_MM - 2 * 20
    )
    set_position(
        title_layout.placeholders[1],
        20,
        60,
        SLIDE_HEIGHT_MM - 80,
        SLIDE_WIDTH_MM - 2 * 20,
    )


def make_presentation(html):
    # init logger
    logger = logging.getLogger(__name__)
    prs = Presentation()
    configure_presentation(prs)

    # コンテキストを変数に保持
    context = {
        "h1": None,
        "h2": None,
        "h3": None,
    }

    # スライド毎にループ
    for slide_html in html.split("<hr />"):

        # デバッグ表示
        logger.info(f"slide html: {slide_html}")

        # 空のスライドをスキップ
        if len(slide_html) == 0:
            continue

        # html をパース
        soup = BeautifulSoup(slide_html, "html.parser")

        # スライドレベルを特定
        slide_level = None
        for tag in ["h1", "h2", "h3"]:
            tag_html = soup.find(tag)
            if tag_html:
                slide_level = tag
                context[tag] = tag_html.get_text()

        # デバッグ表示
        logger.info(f"{context=}")

        # パースしたテキストを保持する変数を作成
        slide_texts = {"title": "", "context": "", "body": ""}

        # レベルに応じてタイトルとボディを設定
        if slide_level:
            title_soup = soup.find(slide_level)
            slide_texts["title"] = title_soup.get_text()
            slide_texts["body"] = title_soup.find_next_siblings()
        else:
            slide_texts["body"] = [soup]

        # パンくずを作成
        if slide_level == "h1":
            slide_texts["context"] = ""
        elif slide_level == "h2":
            slide_texts["context"] = context["h1"]
        elif slide_level == "h3":
            slide_texts["context"] = context["h1"] + " > " + context["h2"]

        # スライドを追加
        if slide_texts["title"]:
            add_slide(prs, slide_texts)
        else:
            logger.warning(f"skip add slide: {slide_texts}")

    return prs


def add_slide(prs, slide_texts):
    # init logger
    logger = logging.getLogger(__name__)
    logger.info(f"{slide_texts=}")

    # レイアウトを取得
    layout = get_layout_by_name(prs, "Title and Content")

    # スライドを追加
    slide = prs.slides.add_slide(layout)

    # title を設定
    title = slide.shapes.title
    title.text = slide_texts["title"]
    title.text_frame.paragraphs[0].font.size = Pt(40)

    # コンテンツを設定
    content = slide.shapes.placeholders[1]  # content
    draw_soup_to_placeholder(content, slide_texts["body"])
    for x in content.text_frame.paragraphs:
        x.font.size = Pt(30)
    slide.notes_slide.notes_text_frame.text = str(slide_texts["body"])


def parse_li(tag, level=1, ul_ol="ol"):
    result = []
    for li_tag in tag.find_all("li", recursive=False):
        result.append((level, li_tag.get_text(strip=True)))
        nested = li_tag.find(ul_ol)
        if nested:
            result.extend(parse_li(nested, level + 1))
    return result


def draw_soup_to_placeholder(ph, soups):
    # init logger
    logger = logging.getLogger(__name__)

    for soup in soups:
        logger.info(f"{soup=}")
        # トップが p の場合
        if soup.name == "p" and len(list(soup.children)) == 1:
            pg = ph.text_frame.add_paragraph()
            pg.text = soup.get_text()
            pg.level = 0
        elif soup.name == "ol":
            li_items = parse_li(soup, ul_ol="ol", level=0)
            logger.info(f"{li_items=}")
            for level, text in li_items:
                pg = ph.text_frame.add_paragraph()
                pg.text = text
                pg.level = level
        elif soup.name == "ul":
            li_items = parse_li(soup, ul_ol="ul", level=0)
            logger.info(f"{li_items=}")
            for level, text in li_items:
                pg = ph.text_frame.add_paragraph()
                pg.text = text
                pg.level = level


def convert_markdown_to_pptx(md_text):
    # docs = markdown_to_json.dictify(md_text)
    html = markdown.markdown(md_text)
    return make_presentation(html)


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
