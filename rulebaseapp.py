from flask import current_app
from bson import ObjectId
from ruleaggregator import RuleAggregator

class RulebaseApp:
    """
    Manages the rulebase application, including saving, retrieving, and deleting rules.
    """

    def __init__(self, db):
        """
        Initializes the RulebaseApp with the given database.
        
        :param db: DatabaseManager instance.
        """
        self.collection = db.get_collection('Rulebase')

    def save_rule(self, rule):
        """
        Saves a rule to the database.
        
        :param rule: RuleAggregator object to be saved.
        """
        current_app.logger.info(f'Saving rule: {rule}')
        self.collection.insert_one(rule.to_dict())

    def get_all_rules(self):
        """
        Retrieves all rules from the database.
        
        :return: List of RuleAggregator objects.
        """
        return [RuleAggregator.from_dict(rule) for rule in self.collection.find()]

    def delete_rule(self, disease_code):
        """
        Deletes a rule from the database based on the disease code.
        
        :param disease_code: Disease code of the rule to be deleted.
        """
        self.collection.delete_one({'disease_code': disease_code})