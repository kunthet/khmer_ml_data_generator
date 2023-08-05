# -*- coding: utf-8 -*-
"""
Created on Sun Aug  6 00:25:19 2023

@author: kunth
"""
import time
from loguru import logger
from text_renderer.dataset import ImgDataset
from text_renderer.render import Render

class DBWriter():
    def __init__( self, render: Render, log_period: float = 1000):
        super().__init__()
        self.log_period = log_period
        self.render = render

    def run(self, save_dir, num_image=100, offset=0):
        
        log_period = max(1, int(self.log_period / 100 * num_image))
        try:
            with ImgDataset(str(save_dir)) as db:
                exist_count = db.read_count()
                count = 0
                logger.info(f"Exist image count in {save_dir}: {exist_count}")
                start = time.time()
                for _ in range(num_image):
                # while True:
                    # m = self.data_queue.get()
                    img, label = self.render()
                    name = "{:09d}".format(exist_count + count)
                    db.write(name, img, label)
                    count += 1
                    if count % log_period == 0:
                        logger.info(
                            f"{(count/num_image)*100:.2f}%({count}/{num_image}) {log_period/(time.time() - start + 1e-8):.1f} img/s"
                        )
                        start = time.time()
                    
                db.write_count(count + exist_count)
                logger.info(f"{(count / num_image) * 100:.2f}%({count}/{num_image})")
                logger.info(f"Finish generate: {count}. Total: {exist_count+count}")
        except Exception as e:
            logger.exception("DBWriterProcess error")
            raise e

