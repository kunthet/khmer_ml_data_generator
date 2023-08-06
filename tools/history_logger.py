# -*- coding: utf-8 -*-
"""
Created on Sun Aug  6 20:27:41 2023

@author: kunth
"""
import json
from pathlib import Path, WindowsPath


class HistoryLogger():
    TEXT_FILE_KEY = 'text_files'
    
    _data: dict = {TEXT_FILE_KEY: {}}
    _file: str
    
    def __init__(self, file: str):
        self._file = str(file)
        self.load()
    
    
    def save_text_file(self, text_file: WindowsPath, offset: int):
        name = text_file.name
        self._data[self.TEXT_FILE_KEY][name] = offset

    
    def save(self, param, value):
        self._data[param] = value
        self.write()        
    
    def write(self):
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
            
    def load(self):
        if not Path(self._file).exists(): 
            self.write()
        else:
            with open(self._file, encoding='utf-8') as f:
                self._data = json.load(f)

    def to_json(self) -> str:
        return json.dumps(self._data, ensure_ascii=False)

    