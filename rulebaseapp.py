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
        rules = []
        for rule in self.collection.find():
            rule['_id'] = str(rule['_id'])  # Convert ObjectId to string
            rules.append(RuleAggregator.from_dict(rule))
        return rules
    

    
    def delete_rule(self, disease_code):
        """
        Deletes a rule from the database based on the disease code.
        
        :param disease_code: Disease code of the rule to be deleted.
        """
        self.collection.delete_one({'disease_code': disease_code})

    def get_rule_by_id(self, rule_id):
        """
        Retrieves a rule from the database by its ID.
        
        :param rule_id: ID of the rule to be retrieved.
        :return: RuleAggregator object if found, None otherwise.
        """
        rule = self.collection.find_one({'_id': ObjectId(rule_id)})
        if rule:
            rule['_id'] = str(rule['_id'])  # Convert ObjectId to string
            return RuleAggregator.from_dict(rule)
        return None

    def update_rule(self, rule_id, category, disease_name, disease_code, rules):
        """
        Updates a rule in the database.
        
        :param rule_id: ID of the rule to be updated.
        :param category: Category of the rule.
        :param disease_name: List of disease names.
        :param disease_code: List of disease codes.
        :param rules: List of rule entries.
        :return: Dictionary indicating success or failure.
        """
        result = self.collection.update_one(
            {'_id': ObjectId(rule_id)},
            {'$set': {
                'category': category,
                'disease_names': disease_name,
                'disease_codes': disease_code,
                'rules': rules
            }}
        )

        if result.modified_count > 0:
            return {'status': 'success', 'message': 'Rule updated successfully'}
        else:
            return {'status': 'error', 'message': 'Failed to update rule'}