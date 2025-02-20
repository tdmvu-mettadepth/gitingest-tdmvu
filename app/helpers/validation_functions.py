import pandas as pd
import json
import re
import warnings
from collections import Counter
warnings.filterwarnings('ignore')

def is_binary(series):
    non_null_series = series.dropna()
    unique_values = non_null_series.unique()
    if len(unique_values) == 2:
        return non_null_series.size == series.size
    return len(unique_values) == 1 and set(unique_values).issubset({0, 1, '0', '1', 'Y', 'N', 'Yes', 'No', True, False, 'M', 'F', 'Male', 'Female'})


def is_datetime(series):
    try:
        pd.to_datetime(series.dropna(), format='mixed',errors='raise')
        return True
    except (ValueError, TypeError):
        return False


def load_states():
    with open('app/data/state_lookup.txt', 'r') as f:
        states = f.readlines()
        states = [state.strip() for state in states]
    return pd.Series(states)

def load_required_columns(roster_type, payer):
    with open('app/data/master_schema.json', 'r') as f:
        master_schema = json.load(f)
    if payer not in master_schema:
        raise ValueError(f'Payer {payer} is not supported')
    if roster_type not in master_schema[payer]:
        raise ValueError(f'Roster type {roster_type} is not supported for payer {payer}')
    
    required_columns = master_schema[payer][roster_type]
    return required_columns

def load_column_categories(PAYER):
    with open('app/data/column_categories.json', 'r') as f:
        column_categories = json.load(f)
    return column_categories[PAYER]

def check_states_present(state_series, column_series):
    satisfied_mask = column_series.isin(state_series)
    satisfied_count = satisfied_mask.sum()
    total_values = len(column_series)
    return satisfied_count > total_values / 2, satisfied_count / total_values, list(column_series[~satisfied_mask].index)

def is_alpha_numeric(series):
    non_null_series = series.dropna()
    satisfied_mask = non_null_series.apply(lambda value: bool(re.match(r'^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z0-9]+$', str(value))))
    satisfied_count = satisfied_mask.sum()
    total_values = len(non_null_series)
    return satisfied_count > total_values / 2, satisfied_count / total_values, list(non_null_series[~satisfied_mask].index)


def check_format(series, patterns):
    cleaned_non_zero = series.dropna()
    
    def check(x):
        if isinstance(x, float):
            x_str = str(int(x))
        else:
            x_str = str(x)
        return any(re.match(pattern, x_str) for pattern in patterns)

    satisfied_mask = cleaned_non_zero.apply(check)
    satisfied_count = satisfied_mask.sum()
    total_values = len(cleaned_non_zero)

    return satisfied_count > total_values / 2, satisfied_count / total_values, list(cleaned_non_zero[~satisfied_mask].index)


def check_phone(series):
    phone_patterns = [r'^[2-9]\d{9}$', r'^\d{3}-\d{3}-\d{4}$']
    return check_format(series, phone_patterns)


def check_tin_ssn(series):
    tin_patterns = [r'^[1-9]\d{8}$', r'^[9]\d{2}-\d{2}-\d{4}$', r'^\d{3}-\d{2}-\d{4}$']
    return check_format(series, tin_patterns)


def check_zip(series):
    zip_patterns = [r'^[1-9]\d{4}$', r'^\d{5}-\d{4}$']
    return check_format(series, zip_patterns)


def check_NPI(series):
    non_null_series = series.dropna()
    def is_valid_npi(value):
        try:
            int_value = int(value)
            return str(int_value).startswith(('1', '2')) and (len(str(int_value)) == 10)
        except (ValueError, TypeError):
            return False
    valid_npi_mask = non_null_series.apply(is_valid_npi)
    satisfied_count = valid_npi_mask.sum()
    total_values = len(non_null_series)
    return satisfied_count > (total_values / 2), satisfied_count / total_values, list(non_null_series[~valid_npi_mask].index)