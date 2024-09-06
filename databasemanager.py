from pymongo import MongoClient
from flask import current_app, request
from ruleaggregator import RuleAggregator, RuleEntry
from conditionanalyser import ConditionAnalyser
import logging
import os
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseManager:
    def __init__(self, uri, db_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def save_rulebase(self, request):
        try:
            disease_category = request.form.get('category')
            disease_names = request.form.getlist('disease_names[]')
            disease_codes = request.form.getlist('disease_codes[]')
            conditions = request.form.to_dict(flat=False)

            rules_data = []

            for i in range(len(disease_names)):
                disease_entry = {
                    'category': disease_category,
                    'disease_name': disease_names[i],
                    'disease_code': disease_codes[i],
                    'rules': []
                }

                rule_index = 1
                while f'conditions[{rule_index}][]' in conditions:
                    rule_entry = {
                        'rule_id': rule_index,
                        'conditions': []
                    }

                    for condition_index in range(len(conditions[f'conditions[{rule_index}][]'])):
                        condition_type = conditions[f'conditions[{rule_index}][]'][condition_index]
                        parameter = conditions[f'parameters[{rule_index}][]'][condition_index]
                        unit = conditions[f'units[{rule_index}][]'][condition_index]
                        age_min = conditions[f'age_min[{rule_index}][]'][condition_index]
                        age_max = conditions[f'age_max[{rule_index}][]'][condition_index]
                        gender = conditions[f'genders[{rule_index}][]'][condition_index]

                        condition_entry = {
                            'type': condition_type,
                            'parameter': parameter,
                            'unit': unit,
                            'age_min': int(age_min) if age_min else None,
                            'age_max': int(age_max) if age_max else None,
                            'gender': gender
                        }

                        if condition_type == 'range':
                            min_value = conditions[f'min_values[{rule_index}][]'][condition_index]
                            max_value = conditions[f'max_values[{rule_index}][]'][condition_index]
                            condition_entry.update({
                                'min_value': float(min_value) if min_value else None,
                                'max_value': float(max_value) if max_value else None
                            })
                        elif condition_type == 'comparison':
                            operator = conditions[f'operators[{rule_index}][]'][condition_index]
                            comparison_value = conditions[f'comparison_values[{rule_index}][]'][condition_index]
                            condition_entry.update({
                                'operator': operator,
                                'comparison_value': float(comparison_value) if comparison_value else None
                            })
                        elif condition_type == 'time-dependent':
                            operator = conditions[f'operators[{rule_index}][]'][condition_index]
                            comparison_time_value = conditions[f'comparison_time_values[{rule_index}][]'][condition_index]
                            time = conditions[f'time_values[{rule_index}][]'][condition_index]
                            condition_entry.update({
                                'operator': operator,
                                'comparison_time_value': float(comparison_time_value) if comparison_time_value else None,
                                'time': time
                            })

                        rule_entry['conditions'].append(condition_entry)

                    disease_entry['rules'].append(rule_entry)
                    rule_index += 1

                rules_data.append(disease_entry)

            for rule_data in rules_data:
                rule = RuleAggregator(
                    rule_data['category'],
                    rule_data['disease_name'],
                    rule_data['disease_code'],
                    [RuleEntry.from_dict(rule_entry) for rule_entry in rule_data['rules']]
                )
                self.save_rule(rule)


        except Exception as e:
            current_app.logger.error(f'Error adding data: {str(e)}')
            return {'status': 'error', 'message': f'Error adding data: {str(e)}'}
        






    def save_lab_values(self, request):
        try:
            patient_id = request.form.get('patient-id')
            age = int(request.form.get('age'))
            gender = request.form.get('gender')
            parameters = request.form.getlist('parameter-name')
            values = request.form.getlist('value')
            units = request.form.getlist('unit')
            valid_untils = request.form.getlist('valid-until')
            times = request.form.getlist('time-lab-value')
            lab_values_data = []
            for i in range(len(parameters)):
                lab_value_data = {
                    'parameter_name': parameters[i],
                    'value': float(values[i]),
                    'unit': units[i],
                    'valid_until': valid_untils[i],
                    'time': times[i]
                }
                lab_values_data.append(lab_value_data)

            collection = self.get_collection('User_Input_Lab_Values')
            existing_patient = collection.find_one({'patient_id': patient_id})
            if existing_patient:
                collection.update_one(
                    {'patient_id': patient_id},
                    {'$push': {'lab_values': {'$each': lab_values_data}}}
                )
            else:
                new_patient_data = {
                    'patient_id': patient_id,
                    'age': age,
                    'gender': gender,
                    'lab_values': lab_values_data
                }
                collection.insert_one(new_patient_data)

            matching_diseases = self.evaluate_lab_values(age, gender, lab_values_data)

            if matching_diseases:
                return {'status': 'success', 'message': 'Lab values saved and evaluated successfully!', 'results': matching_diseases}
            else:
                return {'status': 'success', 'message': 'Lab values saved successfully! No disease match found.', 'results': []}

        except Exception as e:
            current_app.logger.error(f"Error occurred while saving lab values: {e}")
            return {'status': 'error', 'message': str(e)}

    def save_rule(self, rule):
        collection = self.get_collection('Rulebase')
        collection.insert_one(rule.to_dict())

    def evaluate_lab_values(self, patient_age, patient_gender, lab_values):
        try:
            rules = self.get_all_rules()
            logging.debug(f"Fetched {len(rules)} rules for evaluation")

            matching_diseases = []

            for rule in rules:
                logging.debug(f"Evaluating rule for disease: {rule.disease_name}")
                for rule_entry in rule.rules:
                    rule_conditions_met = True
                    for condition in rule_entry.conditions:
                        if not condition.evaluate(patient_age, patient_gender, lab_values):
                            logging.debug(f"Condition not met: {condition}")
                            rule_conditions_met = False
                            break
                    if rule_conditions_met:
                        logging.debug(f"All conditions met for rule entry: {rule_entry}")
                        matching_diseases.append({
                            'disease_code': rule.disease_code,
                            'disease_name': rule.disease_name,
                            'category': rule.category,
                            'matching_rule': rule_entry.to_dict()
                        })
                        break  # Since rules are OR-ed, we can stop checking further rules for this disease

            logging.debug(f"Found {len(matching_diseases)} matching diseases")
            return matching_diseases
        except Exception as e:
            logging.error(f"Error occurred while evaluating lab values: {e}")
            return []

    def get_all_rules(self):
        collection = self.get_collection('Rulebase')
        return [RuleAggregator.from_dict(rule) for rule in collection.find()]