# -*- coding: utf-8 -*-
"""
Created on Sat Aug  5 13:27:21 2023

@author: kunth
"""

import os
from pathlib import Path
from loguru import logger
from joblib import Parallel, delayed
from typing import List
from text_renderer.corpus import Corpus, EnumCorpus, EnumCorpusCfg

from text_renderer.render import Render, KhmerTextRender
from text_renderer.db_writer import DBWriter, DBFileWriter, DBMemoryWriter
from text_renderer.utils.zip_utils import unzip_text
from tools.history_logger import HistoryLogger

CURRENT_DIR     = Path(os.path.abspath(os.path.dirname(__file__))) / 'example_data'
OUT_DIR         = CURRENT_DIR.parent / "output"
DATA_DIR        = CURRENT_DIR
BG_DIR          = DATA_DIR / "bg"
BG_STAMP_DIR    = DATA_DIR / "bg_stamps"
CHAR_DIR        = DATA_DIR / "char"
FONT_DIR        = DATA_DIR / "font"
FONT_LIST_DIR   = DATA_DIR / "font_list"
TEXT_DIR        = DATA_DIR / "text"
ENUM_DIR        = TEXT_DIR / 'khm'
ENUM_ZIP_DIR    = TEXT_DIR / 'khm_7z'


class KhmerEnumCorpus(EnumCorpus):
    def __init__(self, text_file:str, char_file: str):
        super().__init__(
            EnumCorpusCfg(
                text_paths=[text_file],
                filter_by_chars=True,
                chars_file= char_file,
                
                font_dir= FONT_DIR,
                font_list_file= FONT_LIST_DIR / "font_list.txt",
                font_size=(10, 16),
            ))


class TextGenerator:
    db_memory: DBMemoryWriter
    db_writers = []
    def _gen(self, render: Render, corpus: Corpus, count: int, dbWriters: List[DBWriter], hist: HistoryLogger):
        font_text = corpus.sample_at(count)
        img, label = render(font_text)
        name = "{:09d}".format(count)
        # db.write_count(5)
        n = len(dbWriters)
        i = (count + n) % n
        db = dbWriters[i]
        db.write(name, img, label)
        # hist.save(f'data.{name}', label)
        return count
    def _gen_memory(self, render: Render, corpus: Corpus, count: int, db: DBWriter, hist: HistoryLogger):
        font_text = corpus.sample_at(count)
        img, label = render(font_text)
        name = "{:09d}".format(count)
        # db.write_count(5)
        db.write(name, img, label)
        # hist.save(f'data.{name}', label)
        return count
    
    def get_enum_files(self):
        unzip_text(ENUM_ZIP_DIR, ENUM_DIR)
        return [f for f in os.listdir(ENUM_DIR) if f.endswith('.txt')]
    
    
    def generate(self, num_job = 16):
        save_dir = OUT_DIR / "khmer_enum_data"
        history = HistoryLogger(OUT_DIR / 'hist.json')
        text_files = self.get_enum_files()
        
        
        num_image = 1000
        offset = num_image
        
        for f in text_files:
            text_file = ENUM_DIR / f
            
            corpus = KhmerEnumCorpus(text_file, CHAR_DIR / 'khm.txt')
            # corpus = self.get_khmer_enum_corpus(text_file)
            render = KhmerTextRender(BG_DIR)
            line_count = corpus.count()
            
            # self.db_writers = [DBFileWriter(render, save_dir, f'labels_{i}.json')  for i in range(num_job)]
            
            self.db_memory = DBMemoryWriter(render)
            
            # count = 0
            # self._gen(render, db, corpus, count, history)
            
            par = Parallel(n_jobs=num_job, backend="threading")
            file_offset=0
            while corpus.index < line_count-200:
                
                counts = [c+file_offset for c in range(num_job)]
                # self._gen(render, db, corpus, count, history)
                # count += 1
                # Parallel(n_jobs=num_job, backend="threading")(delayed(self._gen)(render, db, corpus, c, history) for c in counts)
                par(delayed(self._gen_memory)(render, corpus, c, self.db_memory, history) for c in counts)
                # db.run(save_dir, num_image)
                # render.corpus.set_offset(offset)
                file_offset += num_job
                offset += num_image
                if file_offset % num_image ==0:
                    print(file_offset)
    
    
    
    
    
if __name__ == '__main__':
    
    gen = TextGenerator()
    gen.generate()