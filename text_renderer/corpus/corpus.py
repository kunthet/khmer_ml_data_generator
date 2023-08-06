import os
import re
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Union, Set

from loguru import logger
from tenacity import retry, stop_after_attempt

from text_renderer.font_manager import FontManager
from text_renderer.config import TextColorCfg, SimpleTextColorCfg
from text_renderer.utils.errors import RetryError, PanicError
from text_renderer.utils import FontText
from text_renderer.utils.utils import load_chars_file


@dataclass
class CorpusCfg:
    # noinspection pyunresolvedreferences
    """
    Base config for corpus

    Parameters
    ----------
        font_dir : path
            font files directory
        font_list_file : path
            font file names to load from **font_dir**, if not provided, all fonts in font_dir will be used
        font_size : tuple[int, int]
            font size in point (min_font_size, max_font_size)
        clip_length : int
            clip :func:`~text_renderer.corpus.Corpus.get_text` output. set **-1** disables clip
        char_spacing : (Union[float, tuple[float, float]])
            Draw character with spacing. If tuple, random choice between [min, max)
            Set -1 to disable
        text_color_cfg : TextColorCfg
            see :class:`~text_renderer.utils.TextColorCfg`. has higher priority than RenderCfg.text_color_cfg
        horizontal : bool
            generate the horizontal(default) or vertical text
            Set False to generate vertical text
    """
    font_dir: Path
    font_size: Tuple[int, int]
    font_list_file: Path = None
    clip_length: int = -1
    char_spacing: Union[float, Tuple[float, float]] = -1
    text_color_cfg: TextColorCfg = SimpleTextColorCfg()
    horizontal: bool = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.__doc__:
            cls.__doc__ = CorpusCfg.__doc__
        else:
            cls.__doc__ += CorpusCfg.__doc__


class Corpus:
    """
    Base class of different corpus. See :class:`~text_renderer.corpus.CorpusCfg` for base configs for corpus.
    """
    
    offset = 0

    def __init__(self, cfg: "CorpusCfg", chars=None):
        self.chars = chars
        self.cfg = cfg
        self.font_manager = FontManager(cfg.font_dir, cfg.font_list_file, cfg.font_size)

    @retry
    def sample(self):
        
        try:
            text = self.get_text()
        except Exception as e:
            logger.exception(e)
            raise RetryError()

        if self.cfg.clip_length != -1 and len(text) > self.cfg.clip_length:
            text = text[: self.cfg.clip_length]
        
        return self.font_manager.apply_font_random(text)
        
        
    @abstractmethod
    def sample_at(self, index: int):
        pass
    
    def set_offset(self, value):
        self.offset = value

    @abstractmethod
    def get_text(self):
        """
        Returns:
            str: text to render
        """
        pass

    @staticmethod
    def filter_by_chars(text, chars_file):
        """
        Filter chars not exist in chars file

        Args:
            text (Union[str, List[str]]): text to filter
            chars_file (Path): one char per line

        Returns:
            Union[str, List[str]]: string(s) removed chars not exist in chars file

        """
        
        if chars_file is None or not chars_file.exists():
            raise PanicError(f"chars_file not exists: {chars_file}")

        chars = load_chars_file(chars_file, log=True)

        logger.info("filtering text by chars...")

        total_count = 0
        filtered_count = 0

        # TODO: find a more efficient way
        chars = ''.join(dict.fromkeys(sorted(chars)))
        
        pattern = f'[^{chars}]'
        # filtered_chars = []
        if isinstance(text, list):
            out = []
            for t in text:
                t = re.sub(pattern, '', t)
                out.append(t)
        else:
            out = re.sub(pattern, '', text)
        logger.info(
            "done filtering"
            # f"Filter {(filtered_count/total_count)*100:.2f}%({filtered_count}) chars in input text。"
            # f"Unique chars({len(set(filtered_chars))}): {set(filtered_chars)}"
        )
        return out
