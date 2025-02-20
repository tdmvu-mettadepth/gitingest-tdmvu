from fuzzywuzzy.fuzz import partial_ratio
from collections import defaultdict
import re
### get the matrix and populate with best matches directly from this function ###


# get the best match for each column
def get_best_match(column, choices):
    column = column.lower()
    column = re.sub(r'[^\w\s]', '', column)
    choices = [choice.lower() for choice in choices]
    
    return partial_ratio(column, choices)

# # get the best match for each column    
# def get_best_matches(columns, choices):
#     matches = defaultdict(list)
#     # clean columns and choices
#     for column in columns:
#         match = get_best_match(column.strip(), choices)
#         matches[column].append(match)
#     return matches

from fuzzywuzzy.fuzz import ratio
def get_best_matches(columns, choices):
    # takes input columns and choices
    # returns a dictionary with incoming column name as key and list of tuples as value
    matches = defaultdict(list)
    # clean columns and choices
    for column in columns:
        max_ratio = 0
        match = ''
        for choice in choices:
            max_ratio = max(max_ratio, ratio(column.lower(), choice.lower()))
            if max_ratio == ratio(column.lower(), choice.lower()):
                match = choice
        matches[column].append((match, max_ratio))
    return matches