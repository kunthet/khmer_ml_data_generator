# -*- coding: utf-8 -*-
"""
Created on Sun Aug  6 00:25:19 2023

@author: kunth
"""
import time
import numpy as np
from typing import List, Dict
from abc import abstractmethod
from loguru import logger
from text_renderer.dataset import ImgDataset
from text_renderer.render import Render

class DBWriter():
    @abstractmethod
    def write(self, name: str, image: np.ndarray, label: str):
        pass
    @abstractmethod
    def write_count(self, count: int):
        pass

class DBMemoryWriter(DBWriter):
    _images : List[Dict[str, np.ndarray]]
    _labels : List[Dict[str, str]]
    
    def __init__(self, render: Render):
        super().__init__()
        self._images = []
        self._labels = []
        
    def write(self, name: str, image: np.ndarray, label: str):
        self._images.append({name: image})
        self._labels.append({name: label})
    
    def write_count(self, count: int):
        pass
    
    def get_images(self) -> Dict[str, np.ndarray()]:
        return {k: v for d in self._images for k, v in d.items()}
    
    def get_labes(self) -> Dict[str, str]:
        return {k: v for d in self._labels for k, v in d.items()}
    
    
    

class DBFileWriter(DBWriter):
    def __init__( self, render: Render, save_dir: str, label_filename: str = None):
        super().__init__()
        self.save_dir = str(save_dir)
        self.render = render
        self.label_filename = label_filename

    def write(self, name: str, image: np.ndarray, label: str):
        try:
            with ImgDataset(self.save_dir, self.label_filename) as db:
                db.write(name, image, label)
                
        except Exception as e:
            logger.exception("DBFielWriter error")
            raise e

    def write_count(self, count: int):
        with ImgDataset(self.save_dir, self.label_filename) as db:
            db.write_count(count)
    
    
    
    def run(self, save_dir, num_image=100, offset=0):
        
        # log_period = max(1, int(self.log_period / 100 * num_image))
        try:
            with ImgDataset(str(save_dir), self.label_filename) as db:
                exist_count = db.read_count()
                count = 0
                logger.info(f"Exist image count in {save_dir}: {exist_count}")
                # start = time.time()
                for _ in range(num_image):
                # while True:
                    # m = self.data_queue.get()
                    img, label = self.render()
                    name = "{:09d}".format(exist_count + count)
                    db.write(name, img, label)
                    count += 1
                    # if count % log_period == 0:
                    #     logger.info(
                    #         f"{(count/num_image)*100:.2f}%({count}/{num_image}) {log_period/(time.time() - start + 1e-8):.1f} img/s"
                    #     )
                    #     start = time.time()
                    
                db.write_count(count + exist_count)
                logger.info(f"{(count / num_image) * 100:.2f}%({count}/{num_image})")
                logger.info(f"Finish generate: {count}. Total: {exist_count+count}")
        except Exception as e:
            logger.exception("DBWriterProcess error")
            raise e

