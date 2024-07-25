# Custom-Nosql-Database-with-Python

this resembles firebase firestore

stores data in a json format in database.json.

read and write rules are stored separately in rules.json..

the read command is read_structure("main_collection", "document", "field")

the write command is write_structure("main_collection", "document", "field", "content")

to read a specific main collection, use read_structure("main_collection")

to read a specific document, use read_structure("main_collection", "document")

to read a specific field, use read_tructure("main_collection", "document", "field")

I am consistently updating the rules and adding more complex rules as well as visualization capabailities among other cool stuff.


I have used flask api to create read and write requests for the database.json

the update_rules.py basically creates a rules section inside rules.json in realtime for every new document or field in a collection

the client_log.py monitors the authentication, and also logs whatever action is taken by users whether its read or write


