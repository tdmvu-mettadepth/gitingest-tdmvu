import pandas as pd
from collections import defaultdict
import re
import warnings
warnings.filterwarnings('ignore')
from app.helpers.validation_functions import check_states_present, is_binary, is_datetime, is_alpha_numeric, check_zip, check_phone, check_NPI, check_tin_ssn, load_states

state_series = load_states()

def classify_columns(df):
    ### clean the code later
    column_types = defaultdict(list)
    for col in df.columns:
        column_data = df[col]
        
        if df[col].isna().all():
            res = {col: 0}
            column_types["EmptyCol"].append(res)
            continue
        # return in response in the form of dictionary from check functions
        if pd.api.types.is_numeric_dtype(column_data):
            if check_NPI(column_data)[0]:
                res = {col: check_NPI(column_data)[1]}
                column_types["NPI"].append(res)
            elif check_tin_ssn(column_data)[0]:
                res = {col: check_tin_ssn(column_data)[1]}
                column_types["TIN"].append(res)
            elif check_phone(column_data)[0]:
                res = {col: check_phone(column_data)[1]}
                column_types["Phone"].append(res)
            elif check_zip(column_data)[0]:
                res = {col: check_zip(column_data)[1]}
                column_types["ZIP"].append(res)
            else:
                res = {col: 1}
                column_types["Numerical"].append(res)

        elif check_tin_ssn(column_data)[0]:
            res = {col: check_tin_ssn(column_data)[1]}
            column_types["TIN"].append(res)
        
        elif check_phone(column_data)[0]:
            res = {col: check_phone(column_data)[1]}
            column_types["Phone"].append(res)
        
        elif check_zip(column_data)[0]:
            res = {col: check_zip(column_data)[1]}
            column_types["ZIP"].append(res)
        
        elif is_alpha_numeric(column_data)[0]:
            res = {col: is_alpha_numeric(column_data)[1]}
            column_types["AlphaNumeric"].append(res)

        elif is_binary(column_data):
            res = {col: 1}
            column_types["Binary"].append(res)
        
        elif is_datetime(column_data):
            res = {col: 1}
            column_types["DateTime"].append(res)
        
        elif check_states_present(state_series, column_data)[0]:
            state_score = check_states_present(state_series, column_data)[1]
            if state_score > 0.8:
                res = {col: state_score}
                column_types["State"].append(res)
        else:
            res = {col: 0}
            column_types["Others"].append(res)

    return column_types