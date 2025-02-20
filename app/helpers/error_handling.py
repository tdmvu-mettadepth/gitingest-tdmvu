from app.helpers.validation_functions import check_states_present, is_alpha_numeric, check_zip, check_phone, check_NPI, check_tin_ssn, load_states
import pandas as pd

#Function to check null values and return the indexes.
def check_empty(column_data, column):
    null_dict = {"null_msg": "", "null_index": ""}
    if column_data.isna().any():
        null_idx = column_data[column_data.isna() | (column_data == '')].index
        null_dict.update({"null_msg": f"{column} have empty values", "null_index": list(null_idx)})
        return null_dict
    else:
        return False

def error_content(invalid_indexes, null_check, column, value_type = None):
    error_dict = {"error_found": "", "error_col": "", "error_msg": "", "error_index": ""}
    if invalid_indexes:
        if null_check:
            error_msg = null_check['null_msg'] + "and " + f"have invalid {value_type} values"
            invalid_indexes = invalid_indexes + null_check['null_index']
            error_dict.update({"error_found": False, "error_col": column, "error_msg": error_msg, "error_index": invalid_indexes})
            return error_dict
        else:
            error_dict.update({"error_found": False, "error_col": column, "error_msg": f"{column} have invalid {value_type} values", "error_index": invalid_indexes})
            return error_dict
    elif null_check:
        error_dict.update({"error_found": False, "error_col": column, "error_msg": null_check['null_msg'], "error_index": null_check['null_index']})
        return error_dict
        
#Function to check the valid and null values and return a messaage and indexes.
def error_check(df, column):

    #loading the states
    state_series = load_states()
    column_data = df[column]
    invalid_indexes = None

    #####  to handle division by zero error 
    #check if the column data is empty
    if column_data.isna().all():
        return {"error_found": False, "error_col": column, "error_msg": f"{column} is empty", "error_index": ""}
    #####  to handle division by zero error
    
    #Calling the function to check if it contains null values
    null_check = check_empty(column_data, column)
    
    #Checking the values are valid NPI values and the column data contains any null values
    npi = check_NPI(column_data)
    if pd.api.types.is_numeric_dtype(column_data) and npi[0]:
        invalid_indexes = npi[2]
        return error_content(invalid_indexes, null_check, column, "NPI")

    #Checking the values are valid TIN SSN values and the column data contains any null values
    tin_ssn = check_tin_ssn(column_data)
    if tin_ssn[0]:
        invalid_indexes = tin_ssn[2]
        return error_content(invalid_indexes, null_check, column, "TIN")
        
    #Checking the values are valid Phone FAX values and the column data contains any null values    
    phone = check_phone(column_data)
    if phone[0]:
        invalid_indexes = phone[2]
        return error_content(invalid_indexes, null_check, column, "Phone/FAX")

    #Checking the values are valid ZipCode values and the column data contains any null values    
    zipcode = check_zip(column_data)
    if zipcode[0]:
        invalid_indexes = zipcode[2]
        return error_content(invalid_indexes, null_check, column, "ZIP")

    #Checking the values are valid AlphaNumeric values and the column data contains any null values    
    alpha_numeric = is_alpha_numeric(column_data)
    if alpha_numeric[0]:
        invalid_indexes = alpha_numeric[2]
        return error_content(invalid_indexes, null_check, column, "AlphaNumeric")

    #Checking the values are valid State values and the column data contains any null values
    states = check_states_present(state_series, column_data)
    if states[0]:
        state_return_value = states[1]
        invalid_indexes = states[2]
        if state_return_value > 0.8:
            return error_content(invalid_indexes, null_check, column, "State")
        
    if null_check:
        return error_content(invalid_indexes, null_check, column)
        
    return False