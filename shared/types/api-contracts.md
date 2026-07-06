# PRISM API Contracts

This document defines the API contracts between frontend and backend.
Both teams must adhere to these contracts.

## Base URL

- Development: http://localhost:8000/api/v1
- Production: https://prism-backend-[hash]-uc.a.run.app/api/v1

## Authentication

All endpoints except /health and /health/live require:
Authorization: Bearer <firebase-id-token>

## Health Endpoints

GET /health
Response: HealthResponse

GET /health/live
Response: { status: "alive" }

## Standard Error Response

{
  "detail": "Human-readable error description"
}