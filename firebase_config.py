import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    # Only initialize if not already initialized
    if not firebase_admin._apps:
        project_id = os.environ.get("FIREBASE_PROJECT_ID")
        private_key = os.environ.get("FIREBASE_PRIVATE_KEY")
        client_email = os.environ.get("FIREBASE_CLIENT_EMAIL")
        
        if project_id and private_key and client_email:
            private_key = private_key.replace("\\n", "\n")
            cred_dict = {
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key,
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            try:
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                print(f"Warning: Firebase initialization failed with provided credentials: {e}")
                return None
        elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            # Fallback to Application Default Credentials
            try:
                firebase_admin.initialize_app()
            except Exception as e:
                print(f"Warning: Firebase initialization failed with default credentials: {e}")
                return None
        else:
            print("Warning: Firebase disabled for local testing. Missing FIREBASE_* env vars.")
            return None
    
    try:
        return firestore.client()
    except Exception as e:
        print(f"Warning: Could not get Firestore client: {e}")
        return None

db = initialize_firebase()
