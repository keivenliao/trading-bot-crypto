# tokenizer_utils.py

from tensorflow.keras.preprocessing.text import tokenizer_from_json
import json

tokenizer_json = """ ... JSON string ... """
tokenizer = tokenizer_from_json(json.loads(tokenizer_json))


def load_tokenizer_from_json(tokenizer_json):
    return tokenizer_from_json(json.loads(tokenizer_json))

def save_tokenizer_to_json(tokenizer, filename):
    tokenizer_json = tokenizer.to_json()
    with open(filename, 'w') as json_file:
        json_file.write(tokenizer_json)
