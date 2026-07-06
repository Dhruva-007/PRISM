# PRISM

**Helping communities choose the best future, not just predict it.**

PRISM is an AI-powered Decision Intelligence System that continuously transforms
multimodal community data into explainable, simulated, and optimized decisions.

## MVP Scenario

Community Health & Environmental Intervention — respiratory illness driven by
air pollution, traffic, weather, and construction activity.

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, MapLibre GL
- **Backend**: FastAPI, Python 3.13, Pydantic v2
- **AI**: Google Vertex AI, Gemini 2.5 Flash
- **Database**: Firestore
- **Auth**: Firebase Authentication
- **Deployment**: Google Cloud Run

## Local Development

### Prerequisites

- Python 3.13+
- Node.js 20+ LTS
- Google Cloud project with billing enabled
- Firebase project

### Backend

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```
cd frontend
npm install
npm run dev
```