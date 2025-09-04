# Multi-agent and Multimodal Fraud Detection Tool for Stock Market

Cortex is a next-generation multiagent and multimodal fraud detection system for securities markets. Built on LangChain orchestration, Retrieval-Augmented Generation (RAG) pipelines, and  LLM, it combines regulatory scraping, historical and current market data analysis, and real-time social media monitoring to deliver explainable fraud detection and investor protection.

## 🎥 Demo Video

[![Watch the demo](https://img.youtube.com/vi/Q-WyjknTGEU/maxresdefault.jpg)](https://www.youtube.com/watch?v=Q-WyjknTGEU)

*Click the thumbnail above to watch the demo on YouTube*


## Features

- **AI Agent Architecture**: Modular agents for audio, video, text, docs, and social media. Perform deepfake checks, sentiment analysis, compliance, and collaborate for holistic risk assessment.
- **Multi-Modal Verification**: Layered checks on uploads—authenticity, fraud patterns, compliance—across all content types. Outputs unified risk score with clear reasoning.
- **Real-Time Multi Platform Monitoring**: Scans Telegram, Reddit for pump-and-dump, fake tips, misinformation. Links threats to market activity and flags instantly.
- **RAG Integration**: Pulls latest rules, advisories, and fraud data from trusted sources to keep AI decisions accurate and context-aware.
- **Explainable Results:**: Every flag includes reasoning with references, showing what was flagged, why, and next steps.

## Tech Stack

### Backend (Python)
- **Backend**: FastAPI, Scikit-learn, Pandas, Numpy
- **Gen AI**: Langchain for LLM Orchestration, RAG, Gemini LLM
- **AI/ML**: Custom Agents, NLP, ChromaDB, Transformers, PyTorch
- **Data Scrapping and Integration**: BeautifulSoup4, lxml, requests, aiohttp
- **APIs**: Telegram, Reddit, Discord, YFinance, Wikipedia
- **Database**: SQLite

### Frontend (React + TypeScript)
- **UI Framework**: React 18
- **Styling**: Tailwind CSS
- **State Management**: React Query
- **Form Handling**: React Hook Form
- **UI Components**: Radix UI

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL (for production)
- API keys for Telegram, Reddit, and Discord

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/AryanMishra1789/Multiagent-and-Multimodal-fraud-detection-tool-for-Stock-Market.git
   cd Multiagent-and-Multimodal-fraud-detection-tool-for-Stock-Market
   ```

2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env` in the backend directory
   - Fill in your API keys and configuration

4. Run the FastAPI server:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

5. Access the API documentation at:
   ```bash
   http://127.0.0.1:8000/docs
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## Project Structure

```
.
├── backend/               # Backend Python code
│   ├── data/             # Data files and databases
│   ├── routes/           # API route handlers
│   ├── utils/            # Utility functions
│   ├── main.py           # Main FastAPI application
│   └── requirements.txt  # Python dependencies
├── frontend/             # Frontend React application
│   ├── public/           # Static files
│   └── src/              # React source code
├── .env.example          # Example environment variables
├── .gitignore           # Git ignore file
└── README.md            # This file
```

## Acknowledgments

- SEBI for regulatory data
- OpenAI for language models
- All open-source libraries used in this project

