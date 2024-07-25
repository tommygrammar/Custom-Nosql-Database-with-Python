import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DATABASE_FILE = 'path to database.json'
RULES_FILE = 'path to rules.json'

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    else:
        return {}

def save_json(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def update_rules(database, rules):
    for user, user_rules in rules.items():
        for collection, collection_rules in database.items():
            if collection not in user_rules:
                user_rules[collection] = {"allow_read": False, "allow_write": False}

            for document, document_fields in collection_rules.items():
                if document not in user_rules[collection]:
                    user_rules[collection][document] = {"allow_read": False, "allow_write": False}

                for field in document_fields:
                    if field not in user_rules[collection][document]:
                        user_rules[collection][document][field] = {"allow_read": False, "allow_write": False}
                        
    return rules



class DatabaseHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == DATABASE_FILE:
            global rules, database
            database = load_json(DATABASE_FILE)
            rules = update_rules(database, rules)
            save_json(rules, RULES_FILE)
            
            print( "Rules updated based on new database entries")

if __name__ == "__main__":
    database = load_json(DATABASE_FILE)
    rules = load_json(RULES_FILE)

    rules = update_rules(database, rules)
    save_json(rules, RULES_FILE)

    event_handler = DatabaseHandler()
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(DATABASE_FILE), recursive=False)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
