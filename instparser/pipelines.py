# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter
from pymongo import MongoClient


class InstparserPipeline:
    def __init__(self):
        self.mb_client = MongoClient('localhost', 27017)
        self.mongobase = self.mb_client['instagram']

    def process_item(self, item, spider):
        collection = self.mongobase[item['collection']]
        del item['collection']
        if list(collection.find({'user': item['user'], 'subject': item['subject']})):
            print('Запись уже существует!')
        collection.update_one({'user': item['user'], 'subject': item['subject']}, {'$set': dict(item)}, upsert=True)

        return item

    def __del__(self):
        self.mb_client.close() # ВОПРОС: Почему с этим вызовом программа зависает на выходе?