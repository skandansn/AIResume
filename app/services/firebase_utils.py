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

def call_firebase_function_and_handle_result(firebase_function, *args, **kwargs):
    try:
        result = firebase_function(*args, **kwargs)
        return result
    except HTTPError as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail="Invalid input. Please try again.")
    except HTTPException:
        # already a well formed API error, so let it through untouched
        raise
    except Exception as e:
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=500, detail="Something terrible happened. Please try again later.")

# AUTHENTICATION
auth = firebase_app.auth()

def firebase_sign_up_with_email_and_password(email, password):
    return call_firebase_function_and_handle_result(auth.create_user_with_email_and_password, email, password)

def firebase_sign_in_with_email_and_password(email, password):
    return call_firebase_function_and_handle_result(auth.sign_in_with_email_and_password, email, password)

def firebase_verify_token(token):
    return auth.verify_id_token(token)

# FIRESTORE
#
# Resume templates used to live in Cloud Storage, but Storage is not available
# on the no-cost Firebase plan, so a template's .tex is now kept as a string on
# the user document alongside its label count. Generated PDFs are returned to
# the caller in the response instead of being uploaded anywhere.
fsdb = firebase_app.firestore()

def firebase_get_user_document(user):
    return call_firebase_function_and_handle_result(
        fsdb.collection("users").document(user.get("user_id")).get,
        token=user.get("logged_in_token"),
    )

def firebase_update_user_document(user, values):
    return call_firebase_function_and_handle_result(
        fsdb.collection("users").document(user.get("user_id")).update,
        values,
        token=user.get("logged_in_token"),
    )

def firebase_update_output_resume_name(user, resume_name):
    return firebase_update_user_document(user, {"output_resume_name": resume_name})

def firebase_get_output_resume_name(user):
    return firebase_get_user_document(user).get("output_resume_name")

def firebase_update_resume_content(user, resume_content, section_items_count):
    return firebase_update_user_document(user, {
        "resume": {
            "content": resume_content,
            "label_count": section_items_count
        }
    })


def firebase_get_resume_content(user):
    return firebase_get_user_document(user).get("resume_content")

def firebase_add_resume_tex_file_to_existing_tex_files(user, tex_file_name, label_count, content):
    # should add the tex file to the existing tex files array if it doesn't already exist. if it does, update the label count and content
    tex_files = firebase_get_tex_files(user)
    if tex_files is None:
        tex_files = []
    tex_file = next((item for item in tex_files if item["file_name"] == tex_file_name), None)
    if tex_file is None:
        tex_files.append({
            "file_name": tex_file_name,
            "label_count": label_count,
            "content": content
        })
    else:
        tex_file["label_count"] = label_count
        tex_file["content"] = content
    return firebase_update_user_document(user, {"tex_files": tex_files})

def firebase_get_tex_files(user):
    return firebase_get_user_document(user).get("tex_files")

def firebase_get_tex_file_content(user, tex_file_name):
    tex_files = firebase_get_tex_files(user) or []
    tex_file = next((item for item in tex_files if item.get("file_name") == tex_file_name), None)
    return tex_file.get("content") if tex_file else None

def firebase_create_user_in_firestore(user, email):
    return call_firebase_function_and_handle_result(
        fsdb.collection("users").document(user.get("localId")).set,
        {"email": email},
        token=user.get("idToken"),
    )

def firebase_get_user_from_firestore(user):
    return firebase_get_user_document(user)
