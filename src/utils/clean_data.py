# def clean_data_recursively(data):
#     if isinstance(data, dict):
#         cleaned_dict = {}
#         for k, v in data.items():
#             cleaned_value = clean_data_recursively(v)
#             if cleaned_value not in ("", None, [], {}) and cleaned_value is not None:
#                 cleaned_dict[k] = cleaned_value
#         return cleaned_dict

#     elif isinstance(data, list):
#         cleaned_list = [clean_data_recursively(item) for item in data if item not in ("", None)]
#         return [item for item in cleaned_list if item not in ("", None, [], {})]

#     else:
#         return data

def clean_data_recursively(data):
    if isinstance(data, dict):
        cleaned_dict = {}
        for k, v in data.items():
            # Special handling for list type to ignore empty list gracefully
            if isinstance(v, list) and not v:
                continue  # skip empty list entirely
            cleaned_value = clean_data_recursively(v)
            if cleaned_value not in ("", None, {}, []):
                cleaned_dict[k] = cleaned_value
        return cleaned_dict

    elif isinstance(data, list):
        # Clean each item and remove invalid entries
        cleaned_list = [clean_data_recursively(item) for item in data if item not in ("", None)]
        return cleaned_list if cleaned_list else None  # return None if list is empty

    else:
        return data
