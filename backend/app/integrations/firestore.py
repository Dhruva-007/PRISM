"""
Firestore client integration for PRISM.

This module initializes the Firebase Admin SDK and provides a Firestore
client singleton. All database operations flow through this client.

The SDK is initialized using a service account key file in development,
and using Application Default Credentials (ADC) in production Cloud Run.
"""

import os
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore as firebase_firestore
from google.cloud.firestore import Client

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _initialize_firebase_app() -> None:
    """
    Initialize Firebase Admin SDK if not already initialized.

    In development: uses service account JSON key file.
    In production: uses Application Default Credentials (ADC),
    which Cloud Run provides automatically via the service account
    attached to the Cloud Run service.
    """
    if firebase_admin._apps:
        return

    settings = get_settings()

    if settings.is_production:
        logger.info("Initializing Firebase Admin SDK with Application Default Credentials")
        cred = credentials.ApplicationDefault()
    else:
        service_account_path = settings.firebase_service_account_path
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(
                f"Firebase service account key not found at: {service_account_path}\n"
                "Download it from Firebase Console → Project Settings → Service Accounts"
            )
        logger.info(
            "Initializing Firebase Admin SDK with service account: %s",
            service_account_path,
        )
        cred = credentials.Certificate(service_account_path)

    firebase_admin.initialize_app(
        cred,
        {"projectId": settings.google_cloud_project_id},
    )
    logger.info("Firebase Admin SDK initialized successfully")


@lru_cache()
def get_firestore_client() -> Client:
    """
    Return a cached Firestore client.

    Initializes Firebase Admin SDK on first call.
    Subsequent calls return the cached client.

    Returns:
        A Firestore Client instance.

    Raises:
        FileNotFoundError: If service account file is missing in development.
        Exception: If Firebase initialization fails.
    """
    _initialize_firebase_app()
    client = firebase_firestore.client()
    logger.info("Firestore client created successfully")
    return client