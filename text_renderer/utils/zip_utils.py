# -*- coding: utf-8 -*-
"""
Created on Sun Aug  6 00:28:24 2023

@author: kunth
"""
import os
from loguru import logger
from pyunpack import Archive

def unzip_text(zipped_folder, text_folder):
    if text_folder.exists(): return
    os.makedirs(text_folder, exist_ok=True)
    zipped_files = [f for f in os.listdir(zipped_folder) if f.endswith('.7z')]
    for f in zipped_files:
        logger.info(f'unzipping: {f}')
        Archive(zipped_folder / f).extractall(text_folder)