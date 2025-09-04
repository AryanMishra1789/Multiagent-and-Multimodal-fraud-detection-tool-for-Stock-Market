# Multi-agent and Multimodal Fraud Detection Tool for Stock Market

A comprehensive fraud detection system that leverages multiple verification agents and data sources to identify potential stock market fraud, including pump-and-dump schemes, fake news, and suspicious corporate announcements.

## 🚀 Features

- **Multi-platform Monitoring**: Tracks Telegram, Reddit, and Discord for suspicious activities
- **Corporate Announcement Analysis**: Verifies corporate announcements against multiple sources
- **Sentiment Analysis**: Detects market manipulation through sentiment analysis
- **Regulatory Compliance**: Cross-references with SEBI database and other regulatory sources
- **Hybrid Verification**: Combines AI and rule-based verification for accurate results
- **Real-time Alerts**: Provides instant notifications for potential fraud cases

## 🛠️ Tech Stack

### Backend (Python)
- **Frameworks**: FastAPI, SQLAlchemy
- **AI/ML**: Transformers, Scikit-learn, PyTorch
- **Data Processing**: Pandas, NumPy
- **APIs**: Telegram, Reddit, Discord, YFinance, Wikipedia
- **Database**: SQLite (development), PostgreSQL (production-ready)

### Frontend (React + TypeScript)
- **UI Framework**: React 18
- **Styling**: Tailwind CSS
- **State Management**: React Query
- **Form Handling**: React Hook Form
- **UI Components**: Radix UI

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL (for production)
- API keys for Telegram, Reddit, and Discord

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/stock-market-fraud-detection.git
   cd stock-market-fraud-detection
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

4. Initialize the database:
   ```bash
   cd backend
   python database_management.py
   ```

5. Run the backend server:
   ```bash
   python main.py
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

## 📊 Project Structure

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

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- SEBI for regulatory data
- OpenAI for language models
- All open-source libraries used in this project

## 📧 Contact

For any queries, please contact [Your Email] or open an issue on GitHub.
