from flask import Flask, request, jsonify, render_template, redirect, url_for
import logging
from bson import ObjectId
from databasemanager import DatabaseManager
from rulebaseapp import RulebaseApp
from ruleaggregator import RuleAggregator, RuleEntry  # Updated import
from conditionanalyser import ConditionAnalyser
import datetime
import logging
import os
import json


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Initialize MongoDB client and access the Project1 database
try:
    db_manager = DatabaseManager('mongodb://172.16.105.132:27017/', 'ExpertSystem')
    rulebase_app = RulebaseApp(db_manager)
    lab_input_user_values_collection = db_manager.get_collection('User_Input_Lab_Values')
except Exception as e:
    app.logger.error(f"Error connecting to MongoDB: {e}")
    exit(1)

class Controller:
    @staticmethod
    @app.route('/')
    def index():
        return render_template('index.html')

    @staticmethod
    @app.route('/about')
    def about():
        return render_template('about.html')

    @staticmethod
    @app.route('/rulebase', methods=['GET', 'POST'])
    def rulebase():
        if request.method == 'POST':
            result = db_manager.save_rulebase(request)
            return jsonify(result), 200 if result['status'] == 'success' else 500

        # Fetch mappings JSON for GET request
        mappings_path = os.path.join(app.root_path, 'static', 'mappings.json')
        icd_mappings_path = os.path.join(app.root_path, 'static', 'sortedIcdMappings.json')

        with open(mappings_path, 'r') as mappings_file:
            mappings = json.load(mappings_file)

        with open(icd_mappings_path, 'r') as icd_mappings_file:
            icd_mappings = json.load(icd_mappings_file)

        return render_template('rulebase.html', mappings=mappings, icd_mappings=icd_mappings)
        


    @staticmethod
    @app.route('/lab_values', methods=['GET', 'POST'])
    def lab_values():
        if request.method == 'POST':
            result = db_manager.save_lab_values(request)
            return jsonify(result), 200 if result['status'] == 'success' else 500
        return render_template('lab_values.html')

    @staticmethod
    @app.route('/view_rulebase', methods=['GET'])
    def view_rulebase():
        try:
            rules = rulebase_app.get_all_rules()
            return render_template('view_rulebase.html', rules=rules)
        except Exception as e:
            app.logger.error(f"Error fetching rules: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @staticmethod
    @app.route('/delete_rule/<disease_code>', methods=['POST'])
    def delete_rule(disease_code):
        try:
            rulebase_app.delete_rule(disease_code)
            return redirect(url_for('view_rulebase'))
        except Exception as e:
            app.logger.error(f"Error deleting rule: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500


@staticmethod
@app.route('/view_patient_data', methods=['GET', 'POST'])
def view_patient_data():
    try:
        # Fetch all patient data from the User_Input_Lab_Values collection
        patient_data = list(lab_input_user_values_collection.find())
        
        # Sort patient data by patient ID
        patient_data.sort(key=lambda x: x['patient_id'])

        if request.method == 'POST':
            patient_id = request.form.get('patient_id')
            if patient_id:
                # Perform binary search to find the patient
                def binary_search(arr, target):
                    low, high = 0, len(arr) - 1
                    while low <= high:
                        mid = (low + high) // 2
                        if arr[mid]['patient_id'] == target:
                            return arr[mid]
                        elif arr[mid]['patient_id'] < target:
                            low = mid + 1
                        else:
                            high = mid - 1
                    return None

                found_patient = binary_search(patient_data, patient_id)
                if found_patient:
                    return render_template('view_patient_data.html', patient_data=[found_patient])
                else:
                    return render_template('view_patient_data.html', patient_data=[], message=f"Patient with ID {patient_id} not found.")

        return render_template('view_patient_data.html', patient_data=patient_data)
    except Exception as e:
        app.logger.error(f"Error fetching patient data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
        

if __name__ == '__main__':
    rules = rulebase_app.get_all_rules()
    app.run(debug=True)