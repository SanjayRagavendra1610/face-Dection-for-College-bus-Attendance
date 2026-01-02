import firebase_admin
from firebase_admin import credentials, firestore
import os

# Firebase is optional - only initialize if firebase_key.json exists
if os.path.exists("firebase_key.json"):
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    # Mock database for offline testing
    print("⚠️  firebase_key.json not found - running in offline mode")
    db = None
