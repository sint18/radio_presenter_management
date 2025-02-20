from firebase_admin import credentials, initialize_app, firestore, storage


# Initialize Firebase
cred = credentials.Certificate("firebase_credentials.json")
initialize_app(cred, {
    "storageBucket": "radio-presenter-520a3.firebasestorage.app"
})
db = firestore.client()
bucket = storage.bucket()