import json
import re
import os

def load_rules(filename='rules.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    else:
        return {}

def check_permissions(rules, collection, document=None, field=None, action='read'):
    if collection not in rules:
        return False
    
    # Check collection level permissions
    collection_rules = rules[collection]
    if action == 'read' and not collection_rules.get('allow_read', False):
        return False
    if action == 'write' and not collection_rules.get('allow_write', False):
        return False
    
    if document:
        # Check document level permissions
        if 'documents' not in collection_rules or document not in collection_rules['documents']:
            return False
        document_rules = collection_rules['documents'][document]
        if action == 'read' and not document_rules.get('allow_read', False):
            return False
        if action == 'write' and not document_rules.get('allow_write', False):
            return False
        
        if field:
            # Check field level permissions
            if 'fields' not in document_rules or field not in document_rules['fields']:
                return False
            field_rules = document_rules['fields'][field]
            if action == 'read' and not field_rules.get('allow_read', False):
                return False
            if action == 'write' and not field_rules.get('allow_write', False):
                return False
    
    return True

def set_structure(main_collection, document, field, content, db):
    if main_collection not in db:
        db[main_collection] = {}
    
    if document not in db[main_collection]:
        db[main_collection][document] = {}
    
    db[main_collection][document][field] = content

    return db

def read_structure(main_collection, document=None, field=None):
    db = load_from_json('database.json')

    if main_collection not in db:
        return f"Main collection '{main_collection}' does not exist."

    if document:
        if document not in db[main_collection]:
            return f"Document '{document}' does not exist in main collection '{main_collection}'."

        if field:
            if field not in db[main_collection][document]:
                return f"Field '{field}' does not exist in document '{document}'."
            return db[main_collection][document][field]
        return db[main_collection][document]
    
    return db[main_collection]

def parse_command(command):
    if command.startswith("set_structure"):
        function_type = "set_structure"
    elif command.startswith("read_structure"):
        function_type = "read_structure"
    else:
        raise ValueError("Invalid command type")

    match = re.search(r'\((.*)\)', command)
    if not match:
        raise ValueError("Invalid command format")

    inside_parentheses = match.group(1)
    arguments = re.findall(r'\"(.*?)\"', inside_parentheses)

    if function_type == "set_structure" and len(arguments) != 4:
        raise ValueError("Please use the correct set structure format")
    elif function_type == "read_structure" and len(arguments) not in [1, 2, 3]:
        raise ValueError("please use the correct read structure format")

    return function_type, arguments

def load_from_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    else:
        return {}

def save_to_json(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def main():
    db_file = 'database.json'
    rules_file = 'rules.json'
    db = load_from_json(db_file)
    rules = load_rules(rules_file)

    command = input("Enter command: ")
    function_type, args = parse_command(command)

    if function_type == "set_structure":
        main_collection, document, field, content = args
        if check_permissions(rules, main_collection, document, field, 'write'):
            db = set_structure(main_collection, document, field, content, db)
            save_to_json(db, db_file)
            print("Data successfully written.")
        else:
            print("Write access is not allowed for this collection/document/field.")
    elif function_type == "read_structure":
        main_collection, document, field = (args + [None, None])[:3]
        if check_permissions(rules, main_collection, document, field, 'read'):
            result = read_structure(main_collection, document, field)
            print(json.dumps(result, indent=4) if isinstance(result, dict) else result)
        else:
            print("Read access is not allowed for this collection/document/field.")

if __name__ == "__main__":
    main()
