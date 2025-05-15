def clean_data_recursively(data):
    if isinstance(data, dict):
        return {
            k: clean_data_recursively(v)
            for k, v in data.items()
            if v not in ("", None) and clean_data_recursively(v) != {}
        }
    elif isinstance(data, list):
        return [
            clean_data_recursively(item)
            for item in data
            if item not in ("", None)
        ]
    else:
        return data
