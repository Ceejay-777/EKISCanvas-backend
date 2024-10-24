from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["MONGO_URI"] = os.getenv("MONGO_URI")

uri = os.getenv("MONGO_URI")
db_name = os.getenv('DB_NAME')

client = MongoClient(uri)
db = client['Notes']

Notes_db = db['Notes']

class Notesdb:
    def __init__(self) -> None:
        self.collection = Notes_db
        
    def get_access_codes(self):
        return self.collection.distinct("access_codes")
    
    def get_all_notes(self, query):
        return self.collection.find_one(query)
    
    def find(self, query, key):
        return self.collection.find_one(query, {key: 1, "_id": 0})
    
    def update_old(self, query, key, newNotes):
        return self.collection.update_one(
            query,
            {"$push": {key: {"$each": newNotes}}}
        )
        
    def create_new(self, query, key, newNotes):
        return self.collection.update_one(
            query,
            {"$set": {key: newNotes}},
            upsert=True  
        )
        
    def delete_note(self, query, key, notes_to_delete):
        return self.collection.update_one(query, {"$pull": {key: notes_to_delete[0]}})

try:
    Notes = Notesdb()
except Exception as e:
    print(f"Error accessing notes collection: {e}")
    raise


@app.get("/api/get_all_access_codes")
def get_all_access_codes():
    all_access_codes = Notes.get_access_codes()
    return jsonify({"message": "success", "access_codes": all_access_codes})

@app.get('/api/confirmCode')
def confirmCode():
    code = request.json.get('code')
    if code not in Notes.get_access_codes('access_code'):
        return jsonify({"error": "Invalid access code. Try again or generate a new one. You will lose all previous notes"}), 401
    return jsonify({"message": "Success"})
    
@app.post('/api/save_notes')
def save_notes():
    data = request.json
    access_code = data.get('access_code')
    day = data.get('day')
    section = data.get('section')
    newNotes = data.get('notes')
    
    if not all([access_code, newNotes, day, section]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    query = {"access_code": access_code}
    key = f'day_{day}.section_{section}'
    document = Notes.find(query, key)
    
    if document and f'day_{day}' in document and f'section_{section}' in document[f'day_{day}']:
        Notes.update_old(query,key, newNotes)
        
    else: 
        Notes.create_new(query,key, newNotes)
    return jsonify({'message': 'Notes saved successfully'}), 200

@app.delete("/api/delete_note")
def delete_note():
    data = request.json
    access_code = data.get('access_code')
    day = data.get('day')
    section = data.get('section')
    notes_to_delete = data.get('notes_to_delete')
    print(access_code, day, section, notes_to_delete)
    
    key = f'day_{day}.section_{section}'
    query = {"access_code": access_code}
    
    result = Notes.delete_note(query, key, notes_to_delete)
    
    if result.modified_count > 0:
        return("Note deleted successfully.")
    else:
        return("Note not found or nothing was deleted.")

@app.get('/api/get_all_notes/<access_code>')
def get_notes(access_code):
    key = {'access_code': access_code}
    notes = Notes.get_all_notes(key)
    if not notes:
        return jsonify({'error': 'Invalid access code'}), 404
    
    notes.pop('_id', None)
    return jsonify(notes), 200

app.debug = True

if __name__ == '__main__':
    app.run(debug=True)