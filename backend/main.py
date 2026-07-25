import os
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import praw
from sentence_transformers import SentenceTransformer
import hdbscan

# Initialize the FastAPI app
app = FastAPI(title="Reddit ClusterFeed", version="1.0")

# For the react frontend to communicate with this backend, we need to allow CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"], # Add your frontend URLs here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IMPORTANT: Replace these with your actual Reddit App credentials from the Developer Portal
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "YOUR_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "YOUR_CLIENT_SECRET")

# The redirect URI must match what you set in your Reddit app settings
REDIRECT_URI = "http://localhost:3000" # Where Reddit sends the user back after login
USER_AGENT = "SubsToCustomFeeds:v1.0 (by /u/Adithya608)"

# Load the sentence transformer model globally so it's ready when requests come in
# (This will download ~80MB the very first time you run it)
print("Loading ML embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded.")

class OAuthCallbackRequest(BaseModel):
    code: str

class CreateFeedsRequest(BaseModel):
    refresh_token: str
    clusters: List[Dict] # Expecting [{ "name": "...", "subreddits": ["..."] }]

@app.post("/api/cluster")
def cluster_user_subreddits(req: OAuthCallbackRequest):
    """
    Exchanges the OAuth code for a token, fetches user subreddits, 
    and runs the clustering algorithm.
    """
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        user_agent=USER_AGENT
    )
    
    try:
        # 1. Exchange the auth code for a refresh token
        refresh_token = reddit.auth.authorize(req.code)
        
        # 2. Fetch the user's subscribed subreddits
        subscribed_subs = list(reddit.user.subreddits(limit=None))
        
        if not subscribed_subs:
            return {"refresh_token": refresh_token, "clusters": []}

        # 3. Build the text corpus (description + title for context)
        sub_names = []
        corpus = []
        for sub in subscribed_subs:
            sub_names.append(sub.display_name)
            text_context = f"{sub.title} {sub.public_description or ''}"
            corpus.append(text_context)
            
        # 4. Generate Vector Embeddings
        raw_embeddings = model.encode(corpus)
        embeddings = np.asarray(raw_embeddings)
        
        # 5. Dynamic Clustering with HDBSCAN
        # min_cluster_size=2 ensures even a tiny niche of 2 subreddits forms a custom feed
        clusterer = hdbscan.HDBSCAN(min_cluster_size=2, min_samples=1, core_dist_n_jobs=1)
        cluster_labels = clusterer.fit_predict(embeddings)
            
        # 6. Group the results
        grouped_data = {}
        for sub_name, cluster_id in zip(sub_names, cluster_labels):
            cluster_id = int(cluster_id)
            if cluster_id not in grouped_data:
                grouped_data[cluster_id] = []
            grouped_data[cluster_id].append(sub_name)
            
        # 7. Format the response for the frontend
        formatted_clusters = []
        feed_counter = 1
        
        for c_id, subs in grouped_data.items():
            if c_id == -1:
                # HDBSCAN labels outliers/noise as -1. We catch these and put them in a Misc feed.
                feed_name = "Misc Subreddits"
                feed_icon = "📌"
            else:
                feed_name = f"Custom Feed {feed_counter}"
                feed_icon = "📦"
                feed_counter += 1
                
            formatted_clusters.append({
                "id": c_id,
                "name": feed_name,
                "icon": feed_icon,
                "subreddits": subs
            })
            
        return {
            "refresh_token": refresh_token,
            "clusters": formatted_clusters
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/save-feeds")
def save_feeds(req: CreateFeedsRequest):
    """
    Takes the generated clusters and saves them as Multireddits on the user's account.
    """
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        refresh_token=req.refresh_token,
        user_agent=USER_AGENT
    )
    
    try:
        existing_multis = reddit.user.multireddits()
        existing_feeds_sets = []
        for multi in existing_multis:
            # multi.subreddits returns a list of Subreddit objects
            sub_names = {sub.display_name.lower() for sub in multi.subreddits}
            existing_feeds_sets.append(sub_names)
    except Exception as e:
        print(f"Error fetching existing multireddits: {e}")
        existing_feeds_sets = []

    results = []
    for cluster in req.clusters:
        feed_name = cluster["name"].replace(" ", "_")
        subreddits = cluster["subreddits"]
        
        # Check if a custom feed with these exact subreddits already exists
        proposed_set = {sub.lower() for sub in subreddits}
        if proposed_set in existing_feeds_sets:
            print(f"Skipping {feed_name}: Custom feed with these subreddits already exists.")
            results.append({"name": cluster["name"], "status": "skipped", "message": "A custom feed for this topic already exists."})
            continue

        try:
            multi = reddit.multireddit.create(
                display_name=cluster["name"],
                subreddits=subreddits,
                description_md="Automatically generated by ClusterFeed."
            )
            # Add to our known existing sets to prevent duplicate creation during this same batch
            existing_feeds_sets.append(proposed_set)
            results.append({"name": cluster["name"], "status": "success"})
        except Exception as e:
            print(f"Error creating {feed_name}: {e}")
            results.append({"name": cluster["name"], "status": "error", "message": str(e)})
            
    return {"results": results}