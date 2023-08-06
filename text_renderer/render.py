from typing import Tuple, List

from PIL import Image
from loguru import logger

import cv2
import numpy as np
from PIL.Image import Image as PILImage
from PIL.ImageFont import FreeTypeFont
from tenacity import retry

from text_renderer.bg_manager import BgManager
from text_renderer.effect import DropoutRand, DropoutVertical, Effects, Line, OneOf
from text_renderer.config import RenderCfg, NormPerspectiveTransformCfg, FixedTextColorCfg
from text_renderer.utils.draw_utils import draw_text_on_bg, transparent_img
from text_renderer.utils import utils
from text_renderer.utils.errors import PanicError
from text_renderer.utils.math_utils import PerspectiveTransform
from text_renderer.utils.bbox import BBox
from text_renderer.utils.font_text import FontText
from text_renderer.utils.types import FontColor, is_list


class Render:
    def __init__(self, render_config: RenderCfg):
        self.render_config = render_config
        self.layout = render_config.layout
        self.bg_manager = BgManager(render_config.bg_dir, render_config.pre_load_bg_img)

    @retry
    def __call__(self, font_text: FontText) -> Tuple[np.ndarray, str]:
        try:
            img, text, cropped_bg, transformed_text_mask = self.gen_single_corpus(font_text)

            if img.size == (0,0): 
                return np.array(img), text
            
            if self.render_config.render_effects is not None:
                img, _ = self.render_config.render_effects.apply_effects(
                    img, BBox.from_size(img.size)
                )

            if self.render_config.return_bg_and_mask:
                gray_text_mask = np.array(transformed_text_mask.convert("L"))
                _, gray_text_mask = cv2.threshold(
                    gray_text_mask, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
                )
                transformed_text_mask = Image.fromarray(255 - gray_text_mask)

                merge_target = Image.new("RGBA", (img.width * 3, img.height))
                merge_target.paste(img, (0, 0))
                merge_target.paste(cropped_bg, (img.width, 0))
                merge_target.paste(
                    transformed_text_mask,
                    (img.width * 2, 0),
                    mask=transformed_text_mask,
                )

                np_img = np.array(merge_target)
                np_img = cv2.cvtColor(np_img, cv2.COLOR_RGBA2BGR)
                np_img = self.norm(np_img)
            else:
                img = img.convert("RGB")
                np_img = np.array(img)
                np_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
                np_img = self.norm(np_img)
            return np_img, text
        except Exception as e:
            logger.exception(e)
            raise e

    def gen_single_corpus(self, font_text: FontText) -> Tuple[PILImage, str, PILImage, PILImage]:
        # font_text = self.corpus.sample()

        bg = self.bg_manager.get_bg()
        text_color =  (255, 50, 0, 255)
        if self.render_config.text_color_cfg is not None:
            text_color = self.render_config.text_color_cfg.get_color(bg)

        char_spacing= -1 #self.corpus.render_config.char_spacing
        text_mask = draw_text_on_bg(font_text, text_color, char_spacing )

        if self.render_config.corpus_effects is not None and text_mask.size != (0, 0):
            text_mask, _ = self.render_config.corpus_effects.apply_effects(
                text_mask, BBox.from_size(text_mask.size)
            )

        if self.render_config.perspective_transform is not None:
            if text_mask.size == (0, 0):
                transformed_text_mask = text_mask
            else:
                transformer = PerspectiveTransform(self.render_config.perspective_transform)
                # TODO: refactor this, now we must call get_transformed_size to call gen_warp_matrix
                _ = transformer.get_transformed_size(text_mask.size)
                
                
                try:
                    (
                        transformed_text_mask,
                        transformed_text_pnts,
                    ) = transformer.do_warp_perspective(text_mask)
                except Exception as e:
                    logger.exception(e)
                    logger.error(font_text.font_path, "text", font_text.text)
                    logger.error(f"text: {font_text.text}")
                    logger.error(f"image size: {text_mask.size}")
                    raise e
        else:
            transformed_text_mask = text_mask

        img, cropped_bg = self.paste_text_mask_on_bg(bg, transformed_text_mask)

        return img, font_text.text, cropped_bg, transformed_text_mask

    def paste_text_mask_on_bg(self, bg: PILImage, transformed_text_mask: PILImage) -> Tuple[PILImage, PILImage]:
        """
        Args:
            bg:
            transformed_text_mask:
        Returns:

        """
        x_offset, y_offset = utils.random_xy_offset(transformed_text_mask.size, bg.size)
        bg = self.bg_manager.guard_bg_size(bg, transformed_text_mask.size)
        bg = bg.crop(
            (
                x_offset,
                y_offset,
                x_offset + transformed_text_mask.width,
                y_offset + transformed_text_mask.height,
            )
        )
        if self.render_config.return_bg_and_mask:
            _bg = bg.copy()
        else:
            _bg = bg
        bg.paste(transformed_text_mask, (0, 0), mask=transformed_text_mask)
        return bg, _bg

    def get_text_color(self, bg: PILImage, text: str, font: FreeTypeFont) -> FontColor:
        # TODO: better get text color
        # text_mask = self.draw_text_on_transparent_bg(text, font)
        np_img = np.array(bg)
        # mean = np.mean(np_img, axis=2)
        mean = np.mean(np_img)

        alpha = np.random.randint(110, 255)
        r = np.random.randint(0, int(mean * 0.7))
        g = np.random.randint(0, int(mean * 0.7))
        b = np.random.randint(0, int(mean * 0.7))
        fg_text_color = (r, g, b, alpha)

        return fg_text_color

    def _should_apply_layout(self) -> bool:
        return isinstance(self.corpus, list) and len(self.corpus) > 1

    def norm(self, image: np.ndarray) -> np.ndarray:
        if self.render_config.gray:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if self.render_config.height != -1 and self.render_config.height != image.shape[0]:
            height, width = image.shape[:2]
            width = int(width // (height / self.render_config.height))
            image = cv2.resize(
                image, (width, self.render_config.height), interpolation=cv2.INTER_CUBIC
            )

        return image



class KhmerTextRender(Render):
    def __init__(self, bg_dir: str):
        super().__init__(RenderCfg(
            bg_dir= bg_dir,
            perspective_transform= NormPerspectiveTransformCfg(20, 20, 1.5),
            gray=True,
            layout_effects=None,
            layout=None,
            height=32,
            corpus_effects=Effects(
                [
                    Line(0.5, color_cfg=FixedTextColorCfg()),
                    OneOf([DropoutRand(p=0.2), DropoutVertical(p=0.2)]),
                ]
            ),
        ))
