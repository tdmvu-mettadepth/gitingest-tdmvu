import json
import pandas as pd
from app.helpers.main_mapping import classify_columns
from app.helpers.fuzzy_match import get_best_matches
from app.helpers.validation_functions import load_required_columns, load_column_categories
from app.helpers.error_handling import error_check
from app.config import settings
from typing import Dict, Any
from fuzzywuzzy import process
from app.services.bert_model import ColumnMapper

ColumnMapper = ColumnMapper()

##### Code Structure needs to be changed #####
def process_file(file_location: str) -> Dict[str, Any]:
    #### with new structures we need to make few chagnes to identify the type of file and process it accordingly ####
    response = {}
    if file_location.endswith(".xlsx"):
        data = None
        sheets = pd.read_excel(file_location, sheet_name=None)
        categories = ['full roster', 'provider add', 'provider term', 'demographic change']
        for i in sheets.keys():
            match = process.extract(i, categories)
            match_score = match[0][1]
            match_name = match[0][0]

            if match_score >= 60 and match_name in categories:
                data = pd.read_excel(file_location, sheet_name=i)
                data.columns = data.columns.str.strip().str.replace('\n', ' ')
                #### This is added to hanle where we have two sheets matching with demographic change ####
                #### and empty sheet has more score than the actual sheet need to handle this case wisely ####
                if response.get(match_name) is None:
                    response[match_name] = standardize_columns(data, match_name)
                elif response[match_name].get('error') is not None:
                    response[match_name] = standardize_columns(data, match_name)
        if data is None:
            raise ValueError("File does not contain Full Roster sheet")
    else:
        raise ValueError("File must be in CSV or Excel format")
    
    # print(response)
    
    return response

def standardize_columns(data, roster_type):
    #### UPDATE :required columns will follow same template for all payers
        # load required columns based on payer ### payer info is hardcoded for now need to fetch from user request
    required_columns = load_required_columns(roster_type, settings.PAYER)
    data = find_exact_table(data, required_columns)
    
    #find action column if present
    action_column = None
    
    get_action = process.extract("action", data.columns)
    print(get_action)



    # clean data columns
    if data is None:
        return {'error': 'No data found in the file', 'mapped_data': [], 'unmatched_columns': required_columns, 'error_columns': required_columns}
    column_categories = load_column_categories(settings.PAYER)
    
    # create matrix to store similarity
    df_similarity = pd.DataFrame(0,columns=data.columns, index=required_columns)
    # get some informatoin aobut the columns based on checks on the data
    incoming_column_types = classify_columns(data)
    # keep only date for datetime columns not the time
    for col in incoming_column_types['DateTime']:
        col = list(col.keys())[0]
        data[col] = pd.to_datetime(data[col]).dt.date
    # in each column category keep only required columns
    for cat in column_categories:
        # filter out columns that are not in required columns
        if column_categories[cat] != []:
            column_categories[cat] = [col for col in column_categories[cat] if col in required_columns]

    #### get the matches using different methods and populate the similarity matrix ####
    
    # using simaese bert model
    matches = {}
    bert_matches = {}
    for cat in column_categories:
        incoming_column_types[cat] = [list(i.keys())[0] for i in incoming_column_types[cat]]
        bert_matches[cat] = ColumnMapper.map_columns(incoming_column_types[cat], column_categories[cat])

    for cat, values in bert_matches.items():
        for value in values:
            df_similarity.loc[value['best_match'], value['incoming_column']] = int(value['score']*100)
            if value['score'] > 0.10:
                print(f"For Category {cat} :  {value['incoming_column']} --> {value['best_match']}  similarity {value['score']}") 

    
    # get best mathces for each column within same category
    
    for cat in column_categories:
        if incoming_column_types[cat] != []:
            if type(incoming_column_types[cat][0]) == dict:
                print("Dict")
                input_columns = [list(col.keys())[0] for col in incoming_column_types[cat]]
                matches[cat] = get_best_matches(input_columns, column_categories[cat])
            else:
                matches[cat] = get_best_matches(incoming_column_types[cat], column_categories[cat])
    
    # flatten mathces
    flat_matches = {}
    for cat in matches.keys():
        for column in matches[cat]:
            flat_matches[column] = matches[cat][column]
    
    for column, match in flat_matches.items():
        df_similarity.loc[match[0][0], column] = match[0][1]
    # do the same thing using all columns and choices
    matches_all = get_best_matches(data.columns, required_columns)
    
    for column, match in matches_all.items():
        matching_column = match[0][0]
        similarity = match[0][1]
        if similarity < 85:
            continue
        # print(f"Matched {column} with {matching_column} with similarity {similarity}")
        df_similarity.loc[match[0][0], column] += match[0][1]

    #### if given column is subset of incoming column then add 81 to similarity ####
    for column in required_columns:
        for incoming_column in data.columns:
            if column.lower() in incoming_column.lower():
                df_similarity.loc[column, incoming_column] += 81
    
    df_similarity.to_csv("similarity.csv")
    #update column names of the data
    #check max similarity for each column
    # make a list of matched columns
    matched_columns = []
    error_columns = []
    
    for _, column in enumerate(data.columns):
        if df_similarity[column].max() > 80:
            new_column = df_similarity[column].idxmax()
            # with open("sample.csv", "a") as f:
            #     f.write(f"{column}, {df_similarity[column].idxmax()}, {df_similarity[column].max()}\n")
            data.rename(columns={column: new_column}, inplace=True) 
            matched_columns.append(df_similarity[column].idxmax())
            df_similarity.loc[df_similarity[column].idxmax(), column] = 0
            
        else:
            if column in incoming_column_types['EmptyCol']:
                error_columns.append({'key': column, 'index': _, 'error': 'Empty Column'})
    
    data.columns = update_column_names(data.columns)
    updated_required_columns = update_column_names(required_columns)

    #Checking the column data is valid or not using required_columns
    for col in updated_required_columns:
        if col in data.columns:
            check = error_check(data, col)
            if check:
                error_columns.append({'key': check['error_col'], 'index': check['error_index'], 'error': check['error_msg']})

    ordered_column = rearrange_columns(data.columns, required_columns)
    data = data[ordered_column]
    data.dropna(how='all', inplace=True)
    data.fillna("", inplace=True)
    
    return {'mapped_data' : data.to_dict(orient='records'), 'unmatched_columns': list(set(required_columns) - set(matched_columns)), 'error_columns': error_columns}    

def find_exact_table(df, required):
    data_found = None
    # first check df.columns for required columns
    columns_found = check_required_columns(required, df.columns)
    if columns_found > len(required) / 2:
        columns = update_column_names(df.columns)
        df.columns = columns
        return df
    for i in range(df.shape[0]):
        #check first 10 rows
        if i > 10:
            break
        #if for any row required columns are found then make that row as the header
        # and take next rows as data
        columns_found = check_required_columns(required, df.iloc[i].values)     
        if columns_found > len(required) / 2:
            columns = df.iloc[i]
            #modify repeated column names by appropriate suffix or prefix    
            columns = update_column_names(columns)
            values = df.iloc[i+1:]
            data_found = pd.DataFrame(values.values, columns=columns)
            data_found.reset_index(drop=True, inplace=True)
            break
    if data_found is None:
        return None
    return data_found

def rearrange_columns(columns, required_columns):
    ordered_columns = []
    remaining_columns = []
    
    for col in columns:
        if col in required_columns:
            ordered_columns.append(col)
        else:
            remaining_columns.append(col)
    ordered_column = ordered_columns + remaining_columns
    return ordered_column


def update_column_names(columns):
    # if column names are repeated then add suffix or prefix
    # for now adding suffix based on number of times column name is repeated
    #### need to update the prefix or suffix based on previous column names ####
    #### e.g Primary Speciality, Board cert,A,B,C, Secondary Speciality, Board cert, A, B, C ####
    #### -> Primary Speciality, Primary Board cert,Primary A, Primary B, Primary C, Secondary Speciality, Secondary Board cert ####
    seen = {}
    # changing the column names within same list was giving error so creating a new list
    # TypeError: Index does not support mutable operations

    new_columns = []
    for i, col in enumerate(columns):
        if col in seen:
            seen[col] += 1

            new_columns.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_columns.append(col)
    return new_columns

def check_required_columns(required, cols):
    match_count = 0
    for i in required:
        match = process.extract(i, cols)
        if match[0][1] > 85:
            match_count += 1
    return match_count