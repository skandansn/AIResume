import firebase
import config.app_configs as settings
from google.cloud.firestore import ArrayUnion
from requests.exceptions import HTTPError
from fastapi import HTTPException
from middleware.logging_middleware import logger

config = {
    "apiKey": settings.settings.firebase_api_key,
    "authDomain": settings.settings.firebase_auth_domain,
    "projectId": settings.settings.firebase_project_id,
    "storageBucket": settings.settings.firebase_storage_bucket,
    "messagingSenderId": settings.settings.firebase_messaging_sender_id,
    "appId": settings.settings.firebase_app_id,
    "measurementId": settings.settings.firebase_measurement_id,
    "databaseURL": settings.settings.firebase_database_url,

    # "serviceAccount": "app/config/firebase_admin_service_account_secrets.json"
}

firebase_app = firebase.Firebase(config)

def call_firebase_function_and_handle_result(firebase_function, *args):
    try:
        result = firebase_function(*args)
        return result
    except HTTPError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail="Invalid input. Please try again.")
    except Exception as e:
        logger.error(e)
        return HTTPException(status_code=500, detail="Something terrible happened. Please try again later.")

# AUTHENTICATION
auth = firebase_app.auth()

def firebase_sign_up_with_email_and_password(email, password):
    return call_firebase_function_and_handle_result(auth.create_user_with_email_and_password, email, password)

def firebase_sign_in_with_email_and_password(email, password):
    return call_firebase_function_and_handle_result(auth.sign_in_with_email_and_password, email, password)

def firebase_verify_token(token):
    return auth.verify_id_token(token)

# STORAGE
storage = firebase_app.storage()

def firebase_download_file_url(file_name):
    return storage.child(file_name).get_url()

def firebase_upload_file(file, file_name):
    storage.child(file_name).put(file)
    return firebase_download_file_url(file_name)

# FIRESTORE
fsdb = firebase_app.firestore()

def firebase_update_output_resume_name(user_id, resume_name):
    return fsdb.collection("users").document(user_id).update({"output_resume_name": resume_name})

def firebase_get_output_resume_name(user_id):
    return fsdb.collection("users").document(user_id).get().get("output_resume_name")

def firebase_update_resume_content(user_id, resume_content, section_items_count):    
    return fsdb.collection("users").document(user_id).update({
        "resume" : {
            "content": resume_content,
            "label_count": section_items_count
        }
    })


def firebase_get_resume_content(user_id):
    return fsdb.collection("users").document(user_id).get().get("resume_content")

def firebase_add_resume_tex_file_to_existing_tex_files(user_id, tex_file_name, label_count):
    return fsdb.collection("users").document(user_id).update({
        "tex_files": ArrayUnion([{"file_name": tex_file_name, "label_count": label_count}])
    })

def firebase_get_tex_files(user_id):
    return fsdb.collection("users").document(user_id).get().get("tex_files")

def firebase_create_user_in_firestore(user_id, email):
    return fsdb.collection("users").document(user_id).set({
        "email": email
    })

def firebase_get_user_from_firestore(user_id):
    return fsdb.collection("users").document(user_id).get()
