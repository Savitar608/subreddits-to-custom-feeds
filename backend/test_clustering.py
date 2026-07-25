import pytest
from unittest.mock import MagicMock, patch
from main import cluster_user_subreddits, OAuthCallbackRequest

# --- 1. Mock Data Setup ---

def create_mock_submission(title):
    """Helper to create a fake Reddit post"""
    mock_post = MagicMock()
    mock_post.title = title
    return mock_post

def create_mock_subreddit(display_name, description, post_titles):
    """Helper to create a fake Subreddit with posts"""
    mock_sub = MagicMock()
    mock_sub.display_name = display_name
    mock_sub.public_description = description
    
    # Mock the 'sub.top()' method to return the fake posts
    mock_sub.top.return_value = [create_mock_submission(title) for title in post_titles]
    return mock_sub

# --- 2. The Tests ---

@patch('main.praw.Reddit') # Intercept the praw.Reddit call in main.py
def test_clustering_logic(mock_praw_reddit):
    # Setup our fake Reddit instance
    mock_reddit_instance = MagicMock()
    mock_praw_reddit.return_value = mock_reddit_instance
    
    # Mock the OAuth exchange to just return a dummy token
    mock_reddit_instance.auth.authorize.return_value = "fake_refresh_token_123"

    # Define our fake subreddits. We will create two distinct topics:
    # Topic A: Programming/Tech
    # Topic B: Fitness
    mock_subs = [
        create_mock_subreddit(
            "reactjs", 
            "A community for learning and developing with React.", 
            ["How to use hooks?", "New React 18 features"]
        ),
        create_mock_subreddit(
            "python", 
            "News about the dynamic, object-oriented programming language Python.", 
            ["FastAPI vs Flask", "Understanding list comprehensions"]
        ),
        create_mock_subreddit(
            "running", 
            "For runners of all abilities.", 
            ["Marathon training plan", "Best shoes for flat feet"]
        ),
        create_mock_subreddit(
            "bodyweightfitness", 
            "A community for calisthenics.", 
            ["My first pullup!", "Routine critique needed"]
        )
    ]
    
    # Tell our fake reddit instance to return these subreddits when asked
    mock_reddit_instance.user.subreddits.return_value = mock_subs

    # --- 3. Execute the Code ---
    
    # Create a dummy request object
    request = OAuthCallbackRequest(code="fake_oauth_code")
    
    # Call the actual API endpoint logic
    response = cluster_user_subreddits(request)

    # --- 4. Assertions ---
    
    assert response["refresh_token"] == "fake_refresh_token_123"
    
    clusters = response["clusters"]
    
    # We expect 2 clusters (Tech and Fitness), plus maybe the -1 Misc cluster
    assert len(clusters) > 0
    
    # Let's find the clusters containing our specific subs
    tech_cluster = None
    fitness_cluster = None
    
    for cluster in clusters:
        subs = cluster["subreddits"]
        if "reactjs" in subs or "python" in subs:
            tech_cluster = cluster
        if "running" in subs or "bodyweightfitness" in subs:
            fitness_cluster = cluster

    # Verify that HDBSCAN successfully separated Tech from Fitness based on our mock text
    assert tech_cluster is not None
    assert fitness_cluster is not None
    assert tech_cluster["id"] != fitness_cluster["id"]
    
    # Verify that reactjs and python ended up in the same group
    assert "reactjs" in tech_cluster["subreddits"]
    assert "python" in tech_cluster["subreddits"]