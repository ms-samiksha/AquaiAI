```markdown
🌊 AquaAI — Marine Ecosystem Intelligence

AI-powered marine species identification and coral reef health monitoring, built with Amazon Nova on AWS Bedrock.

🐠 AWS Hackathon 2026 | 🤖 Amazon Nova | ☁️ AWS Bedrock | 🔗 FastAPI | ⚛️ Next.js

🔗 Links
- Live Demo: https://aquai-ai.vercel.app
- Backend API: https://aquaiai.onrender.com/docs
- Demo Video: https://www.youtube.com/watch?v=WuJ012c3D1c

---

🌟 What It Does

AquaAI identifies any marine creature from a photo and monitors coral reef health in real time.

| Feature             | Description                                                        |
|---------------------|--------------------------------------------------------------------|
| 🐟 Fish ID         | Identify reef fish with confidence scoring, habitat, ecosystem role |
| 🪸 Coral Health    | Detect bleaching severity, danger level, conservation actions       |
| 🦞 Marine Life     | Identify lobsters, crabs, turtles, octopus and more                 |
| 🩺 Health Detection| Detect barnacles, parasites, wounds, fin damage automatically       |
| 💬 AI Chat         | Deep-dive into any species via conversational AI                    |
| 🔍 Species Search  | Text-based search with full ecological profiles                     |

---

## 🏗️ Architecture

**Two-stage AI pipeline:**

User Image Upload
        │
        ▼
┌─────────────────────┐
│  Next.js Frontend   │  ← Vercel
│  (aquai-ai.vercel)  │
└──────────┬──────────┘
           │ REST API
           ▼
┌─────────────────────┐
│  FastAPI Backend    │  ← Render
│  (aquaiai.onrender) │
└──────┬──────────────┘
       │
  ┌────┴─────┐
  ▼          ▼
Stage 1    AWS S3
Vision     Images
Nova        Store
  │
  ▼ features
Stage 2
Species ID
Nova
  │
  ▼
Results

Stage 1 — Vision: Nova sees the image and extracts body shape, color, bleaching %, health observations

Stage 2 — Species ID: Nova receives image + extracted features → returns species name, confidence, health assessment, ecological profile


 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| AI Model | Amazon Nova (multimodal) via AWS Bedrock Converse API |
| Storage | AWS S3 |
| Backend | FastAPI + Python 3.11 |
| Frontend | Next.js 16 + TypeScript + Tailwind CSS |
| Backend Deploy | Render |
| Frontend Deploy | Vercel |

---

 🚀 Local Setup

# Prerequisites
- Python 3.11+
- Node.js 18+
- AWS account with Bedrock enabled
- S3 bucket

# Backend

```bash
cd aquaAI
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create `.env` file:
```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name
```

Run:
```bash
python main.py
# API docs at http://localhost:8000/docs
```

# Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Run:
```bash
npm run dev
# App at http://localhost:3000
```

---

 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze` | Upload image for species ID + health assessment |
| POST | `/search` | Search species by name |
| POST | `/chat` | Chat about an identified species |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

# Example: Analyze Image
```bash
curl -X POST https://aquaiai.onrender.com/analyze \
  -F "file=@fish.jpg" \
  -F "analysis_type=fish"
```

# Example: Search Species
```bash
curl -X POST https://aquaiai.onrender.com/search \
  -H "Content-Type: application/json" \
  -d '{"species_name": "Blue Tang", "analysis_type": "fish"}'
```

---

 📂 Project Structure

```
aquaAI/
├── main.py                    # FastAPI app + CORS
├── schemas.py                 # Pydantic models
├── requirements.txt
├── runtime.txt                # Python 3.11.8 for Render
├── routers/
│   ├── analyze.py             # POST /analyze
│   ├── search.py              # POST /search
│   └── chat.py                # POST /chat
├── services/
│   ├── vision_service.py      # Stage 1 — visual feature extraction
│   ├── species_service.py     # Stage 2 — species ID + health
│   ├── nova_client.py         # AWS Bedrock client
│   └── s3_service.py          # S3 upload + presigned URLs
└── frontend/
    ├── app/
    │   ├── page.tsx            # Home — upload + search tabs
    │   └── results/page.tsx    # Results — species + health + chat
    ├── components/
    │   ├── UploadCard.tsx      # Image upload (fish/coral/marine)
    │   ├── SearchCard.tsx      # Text search
    │   └── ChatPanel.tsx       # AI chat assistant
    └── next.config.js
```
```
---

 🌍 Impact

- Marine conservationists — track reef bleaching events in real time
- Citizen scientists — identify invasive species like Lionfish
- Researchers — monitor fish health and disease spread
- Educators — teach marine biology interactively

With climate change threatening 90% of coral reefs by 2050, accessible tools for reef monitoring have never been more critical.

---

 📝 License

Built for AWS Hackathon 2026. Feel free to modify and extend!

---

AquaAI — Where AI meets the Ocean 🌊
