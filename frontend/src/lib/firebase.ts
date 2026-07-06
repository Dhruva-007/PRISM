/**
 * Firebase Client SDK Configuration for PRISM.
 *
 * Initializes Firebase for browser-side use.
 * Responsibilities:
 * - Firebase Authentication (Google Sign-In)
 * - Obtaining ID tokens to send to the backend
 *
 * This module does NOT directly read from Firestore.
 * All data operations go through the FastAPI backend,
 * which uses the Firebase Admin SDK server-side.
 *
 * Firebase config values are safe to expose in the browser.
 * They identify the project but do not grant any permissions.
 * Security is enforced by Firestore rules and Firebase Auth.
 */

import { initializeApp, getApps, type FirebaseApp } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  type Auth,
} from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY!,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN!,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID!,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET!,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID!,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID!,
};

/**
 * Initialize Firebase app as a singleton.
 * getApps() prevents re-initialization in Next.js hot reload cycles.
 */
function initializeFirebase(): FirebaseApp {
  const existingApps = getApps();
  if (existingApps.length > 0) {
    return existingApps[0];
  }
  return initializeApp(firebaseConfig);
}

const firebaseApp: FirebaseApp = initializeFirebase();

/**
 * Firebase Auth instance for the browser.
 * Used for Google Sign-In and token retrieval.
 */
const auth: Auth = getAuth(firebaseApp);

/**
 * Google OAuth provider configured for PRISM.
 */
const googleProvider = new GoogleAuthProvider();
googleProvider.addScope("email");
googleProvider.addScope("profile");

export { firebaseApp, auth, googleProvider };