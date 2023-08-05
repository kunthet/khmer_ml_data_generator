# -*- coding: utf-8 -*-
"""
Created on Sat Aug  5 13:27:21 2023

@author: kunth
"""

import os
from pathlib import Path
from loguru import logger

from text_renderer.effect import DropoutRand, DropoutVertical, Effects, Line, OneOf
from text_renderer.corpus import EnumCorpus, EnumCorpusCfg
from text_renderer.config import (
    RenderCfg,
    NormPerspectiveTransformCfg,
    FixedTextColorCfg,
)

from text_renderer.render import Render
from text_renderer.db_writer import DBWriter
from text_renderer.utils.zip_utils import unzip_text

CURRENT_DIR = Path(os.path.abspath(os.path.dirname(__file__))) / 'example_data'
# CURRENT_DIR = Path("D:/Dev/ML/text_renderer/example_data")
OUT_DIR = CURRENT_DIR.parent / "output"
DATA_DIR = CURRENT_DIR
BG_DIR = DATA_DIR / "bg"
BG_STAMP_DIR = DATA_DIR / "bg_stamps"
CHAR_DIR = DATA_DIR / "char"
FONT_DIR = DATA_DIR / "font"
FONT_LIST_DIR = DATA_DIR / "font_list"
TEXT_DIR = DATA_DIR / "text"
# KHM_CHAR= Path("D:/Dev/ML/text_renderer/example_data/char/khm.txt")
# KHM_TEXT= Path("C:/temps/ML-data/post_db_cleaned_fixed_char_order.txt")
# KHM_ENUM= Path("C:/temps/ML-data/lines_128c_part_0.txt")

perspective_transform = NormPerspectiveTransformCfg(20, 20, 1.5)

font_cfg = dict(
    font_dir=FONT_DIR,
    font_list_file=FONT_LIST_DIR / "font_list.txt",
    font_size=(10, 16),
)

def get_khmer_enum_corpus(enum_file: str):
    return EnumCorpus(
        EnumCorpusCfg(
            text_paths=[enum_file],
            filter_by_chars=True,
            chars_file= CHAR_DIR / 'khm.txt',
            **font_cfg
        ),
        random=False,
    )


def base_config(corpus, corpus_effects=None, layout_effects=None, layout=None, gray=True):
    return RenderCfg(
        bg_dir=BG_DIR,
        perspective_transform=perspective_transform,
        gray=gray,
        layout_effects=layout_effects,
        layout=layout,
        corpus=corpus,
        corpus_effects=corpus_effects,
        height=32,
    )

def khm_config(enum_file: str):
    return base_config(
        corpus=get_khmer_enum_corpus(enum_file),
        corpus_effects=Effects(
            [
                Line(0.5, color_cfg=FixedTextColorCfg()),
                OneOf([DropoutRand(), DropoutVertical()]),
            ]
        ),
    )




text_folder = TEXT_DIR / 'khm'
zipped_folder = TEXT_DIR / 'khm_7z'
unzip_text(zipped_folder, text_folder)

save_dir = OUT_DIR / "khmer_enum_data"
text_files = [f for f in os.listdir(text_folder) if f.endswith('.txt')]

num_image = 1000
offset = num_image

for f in text_files:
    text_file = text_folder / f
    render = Render(khm_config(text_file))
    line_count = render.corpus.count()
    
    while render.corpus.index < line_count-200:
        db = DBWriter(render, log_period=100)
        db.run(save_dir, num_image)
        # render.corpus.set_offset(offset)
        offset += num_image



