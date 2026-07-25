# Reddit ClusterFeed

An AI-powered web application that automatically groups your Reddit subscriptions into thematic **Custom Feeds** (multireddits) using machine learning. Instead of manually sorting subreddits, this tool dynamically clusters subreddits by topic, tone, and semantic similarity.

---

## Features

- **Reddit OAuth 2.0 Integration**: Secure login without sharing account credentials.
- **Semantic Clustering**: Uses sentence embeddings and density-based clustering (`HDBSCAN`) to automatically discover thematic groups.
- **Automatic Multireddit Creation**: Generates and syncs new Custom Feeds directly to your Reddit account.
- **Duplicate Feed Prevention**: Automatically checks existing custom feeds on your account and safely skips creation if a feed with identical subreddits already exists.
- **Outlier Handling**: Groups unclustered or unique subreddits into a dedicated "Misc" feed.

---

## Tech Stack

### Frontend
- **Framework**: React (Vite 8)
- **Styling**: Tailwind CSS
- **API Communication**: Fetch API

### Backend
- **Framework**: Python (FastAPI)
- **Machine Learning**: `sentence-transformers`, `HDBSCAN`, `scikit-learn`
- **Reddit API Wrapper**: `praw`
- **Testing**: `pytest`, `unittest.mock`

---

## Getting Started

### Prerequisites

- **Node.js**: v18+
- **Python**: 3.10+
- **Reddit App Credentials**: Create a "script" or "web app" in the [Reddit App Preferences](https://www.reddit.com/prefs/apps).

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Savitar608/subreddits-to-custom-feeds.git
cd subreddits-to-custom-feeds
```

### 2. Backend Setup

```bash
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
```

Configure your `.env` file with your Reddit developer credentials:

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_REDIRECT_URI=http://localhost:3000/callback
```

Run the backend server:

```bash
uvicorn main:app --reload --port 8000
```

*(Note: The first time you run this, it will pause to download the Hugging Face sentence transformer model.)*

### 3. Frontend Setup

In a new terminal window:

```bash
cd frontend

# Install dependencies
npm install

# Start the Vite development server
npm run dev
```

The frontend will start at `http://localhost:3000`.

---

## Testing

You can verify the machine learning pipeline and clustering logic without needing an active Reddit API key. The backend includes tests that mock the Reddit API responses using predefined data.

```bash
cd backend
pytest test_clustering.py -v
```

---

## How It Works

1. **Authentication**: Log in with your Reddit account via OAuth 2.0 with `mysubreddits`, `read`, and `subscribe` scopes.
2. **Fetch Subreddits**: The backend retrieves your list of subscribed subreddits along with their titles and public descriptions.
3. **Embeddings & Clustering**:
- Subreddit descriptions are mapped to high-dimensional mathematical vectors using `sentence-transformers`.
- `HDBSCAN` clusters these vectors based on spatial semantic density.


4. **Feed Generation**: The app presents the suggested clusters. When you export them, the backend checks your Reddit account to prevent duplicate feeds before generating new Custom Feeds natively on your account.

---

## License

This project is licensed under the [MIT License](https://www.google.com/search?q=LICENSE).