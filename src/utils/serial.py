from datetime import datetime
from bson import ObjectId


def serial_doc(doc):
    if isinstance(doc, list):
        return [serial_doc(item) for item in doc]
    elif isinstance(doc, dict):
        return {k: serial_doc(v) for k, v in doc.items()}
    elif isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime):
        return doc.isoformat()
    else:
        return doc