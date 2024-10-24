from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["MONGO_URI"] = os.getenv("MONGO_URI")
DB_NAME = os.getenv('DB_NAME')

try:
    mongo = PyMongo(app)
    mongo.db.command('ping')
    print("Connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise

try:
    Notes = mongo.db.notes
except Exception as e:
    print(f"Error accessing notes collection: {e}")
    raise


@app.get("/api/get_all_access_codes")
def get_all_access_codes():
    all_access_codes = Notes.distinct("access_codes")
    return jsonify({"message": "success", "access_codes": all_access_codes})

@app.get('/api/confirmCode')
def confirmCode():
    code = request.json.get('code')
    if code not in mongo.db.notes.distinct('access_code'):
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
    document = Notes.find_one(query, {key: 1, "_id": 0})
    
    if document and f'day_{day}' in document and f'section_{section}' in document[f'day_{day}']:
        Notes.update_one(
            query,
            {"$push": {key: {"$each": newNotes}}}
        )
        
    else: 
        Notes.update_one(
            query,
            {"$set": {key: newNotes}},
            upsert=True  
        )
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
    print
    query = {"access_code": access_code}
    
    result = Notes.update_one(query, {"$pull": {key: notes_to_delete[0]}})
    
    if result.modified_count > 0:
        return("Note deleted successfully.")
    else:
        return("Note not found or nothing was deleted.")

@app.get('/api/get_all_notes/<access_code>')
def get_notes(access_code):
    notes = mongo.db.notes.find_one({'access_code': access_code})
    if not notes:
        return jsonify({'error': 'Invalid access code'}), 404
    
    notes.pop('_id', None)
    return jsonify(notes), 200

app.debug = True

if __name__ == '__main__':
    app.run(debug=True)