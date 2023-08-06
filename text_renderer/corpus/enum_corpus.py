from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import numpy as np
from loguru import logger
from text_renderer.utils.errors import PanicError
from text_renderer.utils.utils import random_choice

from .corpus import Corpus, CorpusCfg


@dataclass
class EnumCorpusCfg(CorpusCfg):
    """
    Enum corpus config

    args:
        text_paths (List[Path]): Text file paths
        items (List[str]): Texts to choice. Only works if text_paths is empty
        num_pick (int): Random choice {count} item from texts
        filter_by_chars (bool): If True, filtering text by character set
        chars_file (Path): Character set
        filter_font (bool): Only work when filter_by_chars is True. If True, filter font file
                            by intersection of font support chars with chars file
        filter_font_min_support_chars (int): If intersection of font support chars with chars file is lower
                                             than filter_font_min_support_chars, filter this font file.
        join_str (str):

    """

    text_paths: List[Path] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    num_pick: int = 1
    filter_by_chars: bool = False
    chars_file: Path = None
    filter_font: bool = False
    filter_font_min_support_chars: int = 100
    join_str: str = ""


class EnumCorpus(Corpus):
    """
    Randomly select items from the list
    """
    index : int = 0
    random: bool = True
    
    def __init__(self, cfg: "CorpusCfg", random: bool = True):
        super().__init__(cfg)
        
        self.random = random
        self.cfg: EnumCorpusCfg
        
        if len(self.cfg.text_paths) == 0 and len(self.cfg.items) == 0:
            raise PanicError("text_paths or items must not be empty")

        if len(self.cfg.text_paths) != 0 and len(self.cfg.items) != 0:
            raise PanicError("only one of text_paths or items can be set")

        self.texts: List[str] = []

        if len(self.cfg.text_paths) != 0:
            for text_path in self.cfg.text_paths:
                with open(str(text_path), "r", encoding="utf-8") as f:
                    for line in f.readlines():
                        self.texts.append(line.strip())

        elif len(self.cfg.items) != 0:
            self.texts = self.cfg.items

        if self.cfg.chars_file is not None:
            self.font_manager.update_font_support_chars(self.cfg.chars_file)

        if self.cfg.filter_by_chars:
            self.texts = Corpus.filter_by_chars(self.texts, self.cfg.chars_file)
            if self.cfg.filter_font:
                self.font_manager.filter_font_path(
                    self.cfg.filter_font_min_support_chars
                )
        self._count = len(self.texts)
                
    def count(self):
        return self._count
    
    def sample_at(self, index: int):
        if (index <0 or index >= self._count):
            raise ValueError(f'Index out of range. Index: {index} not in range({self._count})')
        text = self.texts[index]
        return self.font_manager.apply_font_random(text)
        
    def get_text(self):
        if self.random:
            text = random_choice(self.texts, self.cfg.num_pick)
        else:
            start = self.index + self.offset
            end = start + self.cfg.num_pick
            end = min(end, len(self.texts))
            if (start >= end) : 
                self.index += self.cfg.num_pick
                raise IndexError(f'Requested index ({start}) is larger than the available text ({len(self.texts)})')
            text = self.texts[start:end]
            self.index += self.cfg.num_pick
        return self.cfg.join_str.join(text)
