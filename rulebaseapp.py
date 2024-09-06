from flask import current_app
from bson import ObjectId
from ruleaggregator import RuleAggregator

class RulebaseApp:
    def __init__(self, db):
        self.collection = db.get_collection('Rulebase')

    def save_rule(self, rule):
        current_app.logger.info(f'Saving rule: {rule}')
        self.collection.insert_one(rule.to_dict())

    def get_all_rules(self):
        return [RuleAggregator.from_dict(rule) for rule in self.collection.find()]

    def delete_rule(self, disease_code):
        self.collection.delete_one({'disease_code': disease_code})