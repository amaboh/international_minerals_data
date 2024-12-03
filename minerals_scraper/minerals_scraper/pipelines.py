import os

class MineralsDownloadPipeline:
    def process_item(self, item, spider):
        if 'file_path' in item and os.path.exists(item['file_path']):
            file_size = os.path.getsize(item['file_path'])
            spider.logger.info(f"Successfully downloaded {item['file_path']} ({file_size} bytes)")
        return item