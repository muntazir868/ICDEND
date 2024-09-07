import logging
from abc import ABC, abstractmethod
import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ConditionAnalyser(ABC):
    """
    Abstract base class for condition analysis.
    Defines the interface for evaluating conditions based on patient data.
    """

    @abstractmethod
    def evaluate(self, patient_age, patient_gender, lab_values):
        """
        Abstract method to evaluate the condition based on patient data.
        
        :param patient_age: Age of the patient.
        :param patient_gender: Gender of the patient.
        :param lab_values: List of lab values for the patient.
        :return: Boolean indicating whether the condition is met.
        """
        pass

    @staticmethod
    def from_dict(condition_data):
        """
        Factory method to create a condition object from a dictionary.
        
        :param condition_data: Dictionary containing condition data.
        :return: Instance of the appropriate condition class.
        :raises ValueError: If the condition type is unknown.
        """
        condition_type = condition_data.get('type')
        if condition_type == 'timedependent':
            condition_type = 'time-dependent'

        if condition_type == 'range':
            return RangeCondition(condition_data)
        elif condition_type == 'comparison':
            return ComparisonCondition(condition_data)
        elif condition_type == 'time-dependent':
            return TimeDependentCondition(condition_data)
        else:
            raise ValueError(f"Unknown condition type: {condition_type}")

    def to_dict(self):
        """
        Converts the condition object to a dictionary.
        
        :return: Dictionary representation of the condition.
        """
        return {
            'type': self.__class__.__name__.lower().replace('condition', ''),
            'parameter': self.parameter,
            'unit': self.unit,
            'age_min': self.age_min,
            'age_max': self.age_max,
            'gender': self.gender
        }

class RangeCondition(ConditionAnalyser):
    """
    Condition class for evaluating whether a lab value falls within a specified range.
    """

    def __init__(self, condition_data):
        """
        Initializes the RangeCondition with the given condition data.
        
        :param condition_data: Dictionary containing condition data.
        """
        self.min_value = condition_data.get('min_value')
        self.max_value = condition_data.get('max_value')
        self.parameter = condition_data.get('parameter')
        self.unit = condition_data.get('unit')
        self.age_min = condition_data.get('age_min')
        self.age_max = condition_data.get('age_max')
        self.gender = condition_data.get('gender')

    def evaluate(self, patient_age, patient_gender, lab_values):
        """
        Evaluates whether the patient's lab values meet the range condition.
        
        :param patient_age: Age of the patient.
        :param patient_gender: Gender of the patient.
        :param lab_values: List of lab values for the patient.
        :return: Boolean indicating whether the condition is met.
        """
        logging.debug(f"Evaluating RangeCondition for patient age: {patient_age}, gender: {patient_gender}")
        
        if not (self.age_min <= patient_age <= self.age_max):
            logging.debug(f"Patient age {patient_age} is outside the range [{self.age_min}, {self.age_max}]")
            return False
        if self.gender != 'all' and self.gender != patient_gender:
            logging.debug(f"Patient gender {patient_gender} does not match condition gender {self.gender}")
            return False

        for lab_value in lab_values:
            if lab_value['parameter_name'].lower() == self.parameter.lower() and lab_value['valid_until'] >= str(datetime.date.today()):
                if self.min_value <= lab_value['value'] <= self.max_value:
                    logging.debug(f"Condition met for parameter {self.parameter} with value {lab_value['value']}")
                    return True
        logging.debug(f"Condition not met for parameter {self.parameter}")
        return False

    def to_dict(self):
        """
        Converts the RangeCondition object to a dictionary.
        
        :return: Dictionary representation of the RangeCondition.
        """
        data = super().to_dict()
        data.update({
            'min_value': self.min_value,
            'max_value': self.max_value
        })
        return data

class ComparisonCondition(ConditionAnalyser):
    """
    Condition class for evaluating whether a lab value meets a comparison condition.
    """

    def __init__(self, condition_data):
        """
        Initializes the ComparisonCondition with the given condition data.
        
        :param condition_data: Dictionary containing condition data.
        """
        self.operator = condition_data.get('operator')
        self.comparison_value = condition_data.get('comparison_value')
        self.parameter = condition_data.get('parameter')
        self.unit = condition_data.get('unit')
        self.age_min = condition_data.get('age_min')
        self.age_max = condition_data.get('age_max')
        self.gender = condition_data.get('gender')

    def evaluate(self, patient_age, patient_gender, lab_values):
        """
        Evaluates whether the patient's lab values meet the comparison condition.
        
        :param patient_age: Age of the patient.
        :param patient_gender: Gender of the patient.
        :param lab_values: List of lab values for the patient.
        :return: Boolean indicating whether the condition is met.
        """
        logging.debug(f"Evaluating ComparisonCondition for patient age: {patient_age}, gender: {patient_gender}")
        
        if not (self.age_min <= patient_age <= self.age_max):
            logging.debug(f"Patient age {patient_age} is outside the range [{self.age_min}, {self.age_max}]")
            return False
        if self.gender != 'all' and self.gender != patient_gender:
            logging.debug(f"Patient gender {patient_gender} does not match condition gender {self.gender}")
            return False

        for lab_value in lab_values:
            if lab_value['parameter_name'].lower() == self.parameter.lower() and lab_value['valid_until'] >= str(datetime.date.today()):
                if self.compare_values(lab_value['value']):
                    logging.debug(f"Condition met for parameter {self.parameter} with value {lab_value['value']}")
                    return True
        logging.debug(f"Condition not met for parameter {self.parameter}")
        return False

    def compare_values(self, value):
        """
        Compares the given value with the comparison value based on the operator.
        
        :param value: Value to compare.
        :return: Boolean indicating whether the comparison is true.
        """
        if self.operator == 'greater':
            return value > self.comparison_value
        elif self.operator == 'less':
            return value < self.comparison_value
        elif self.operator == 'equal':
            return value == self.comparison_value
        elif self.operator == 'greater or equal':
            return value >= self.comparison_value
        elif self.operator == 'less or equal':
            return value <= self.comparison_value
        return False

    def to_dict(self):
        """
        Converts the ComparisonCondition object to a dictionary.
        
        :return: Dictionary representation of the ComparisonCondition.
        """
        data = super().to_dict()
        data.update({
            'operator': self.operator,
            'comparison_value': self.comparison_value
        })
        return data

class TimeDependentCondition(ConditionAnalyser):
    """
    Condition class for evaluating whether lab values meet a time-dependent condition.
    """

    def __init__(self, condition_data):
        """
        Initializes the TimeDependentCondition with the given condition data.
        
        :param condition_data: Dictionary containing condition data.
        """
        self.operator = condition_data.get('operator')
        self.comparison_time_value = condition_data.get('comparison_time_value')
        self.time = condition_data.get('time')
        self.parameter = condition_data.get('parameter')
        self.unit = condition_data.get('unit')
        self.age_min = condition_data.get('age_min')
        self.age_max = condition_data.get('age_max')
        self.gender = condition_data.get('gender')

    def evaluate(self, patient_age, patient_gender, lab_values):
        """
        Evaluates whether the patient's lab values meet the time-dependent condition.
        
        :param patient_age: Age of the patient.
        :param patient_gender: Gender of the patient.
        :param lab_values: List of lab values for the patient.
        :return: Boolean indicating whether the condition is met.
        """
        logging.debug(f"Evaluating TimeDependentCondition for patient age: {patient_age}, gender: {patient_gender}")
        
        if not (self.age_min <= patient_age <= self.age_max):
            logging.debug(f"Patient age {patient_age} is outside the range [{self.age_min}, {self.age_max}]")
            return False
        if self.gender != 'all' and self.gender != patient_gender:
            logging.debug(f"Patient gender {patient_gender} does not match condition gender {self.gender}")
            return False

        relevant_lab_values = [
            lv for lv in lab_values
            if lv['parameter_name'].lower() == self.parameter.lower()
        ]

        logging.debug(f"Found {len(relevant_lab_values)} relevant lab values for parameter {self.parameter}")

        relevant_lab_values.sort(key=lambda x: datetime.datetime.strptime(x['time'], '%Y-%m-%d'))

        if len(relevant_lab_values) < 2:
            logging.debug("Less than 2 relevant lab values found, cannot evaluate time-dependent condition")
            return False

        for i in range(len(relevant_lab_values) - 1):
            for j in range(i + 1, len(relevant_lab_values)):
                time_diff = (datetime.datetime.strptime(relevant_lab_values[j]['time'], '%Y-%m-%d') -
                             datetime.datetime.strptime(relevant_lab_values[i]['time'], '%Y-%m-%d')).days

                logging.debug(f"Comparing lab values at times {relevant_lab_values[i]['time']} and {relevant_lab_values[j]['time']}, time difference: {time_diff} days")

                if time_diff >= int(self.time):
                    if self.compare_values(relevant_lab_values[i]['value']) and \
                       self.compare_values(relevant_lab_values[j]['value']):
                        logging.debug("Time-dependent condition met")
                        return True
        logging.debug("Time-dependent condition not met")
        return False

    def compare_values(self, value):
        """
        Compares the given value with the comparison time value based on the operator.
        
        :param value: Value to compare.
        :return: Boolean indicating whether the comparison is true.
        """
        if self.operator == 'greater':
            return value > self.comparison_time_value
        elif self.operator == 'less':
            return value < self.comparison_time_value
        elif self.operator == 'equal':
            return value == self.comparison_time_value
        elif self.operator == 'greater or equal':
            return value >= self.comparison_time_value
        elif self.operator == 'less or equal':
            return value <= self.comparison_time_value
        return False

    def to_dict(self):
        """
        Converts the TimeDependentCondition object to a dictionary.
        
        :return: Dictionary representation of the TimeDependentCondition.
        """
        data = super().to_dict()
        data.update({
            'operator': self.operator,
            'comparison_time_value': self.comparison_time_value,
            'time': self.time
        })
        return data