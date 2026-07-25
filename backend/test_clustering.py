import pytest
from unittest.mock import MagicMock, patch
from main import cluster_user_subreddits, OAuthCallbackRequest

# --- 1. Mock Data Setup ---

def create_mock_subreddit(display_name, title, description):
    """Helper to create a fake Subreddit"""
    mock_sub = MagicMock()
    mock_sub.display_name = display_name
    mock_sub.title = title
    mock_sub.public_description = description
    return mock_sub

# --- 2. The Tests ---

@patch('main.praw.Reddit') # Intercept the praw.Reddit call in main.py
def test_clustering_logic(mock_praw_reddit):
    # Setup our fake Reddit instance
    mock_reddit_instance = MagicMock()
    mock_praw_reddit.return_value = mock_reddit_instance
    
    # Mock the OAuth exchange to just return a dummy token
    mock_reddit_instance.auth.authorize.return_value = "fake_refresh_token_123"

    # Define our fake subreddits. 
    # We provide 4 Tech and 4 Fitness subs to see if HDBSCAN can separate them into distinct clusters based on their descriptions.
    mock_subs = [
        # Topic A: Programming/Tech
        create_mock_subreddit("reactjs", "React", "A community for learning and developing with React, a JS library."),
        create_mock_subreddit("javascript", "JavaScript", "All about the JavaScript programming language."),
        create_mock_subreddit("python", "Python", "News about the dynamic, object-oriented programming language Python."),
        create_mock_subreddit("programming", "Programming", "Computer programming discussions."),
        
        # Topic B: Fitness
        create_mock_subreddit("running", "Running", "For runners of all abilities."),
        create_mock_subreddit("bodyweightfitness", "Bodyweight Fitness", "A community for calisthenics and bodyweight exercises."),
        create_mock_subreddit("weightlifting", "Weightlifting", "Discussions about olympic weightlifting and strength."),
        create_mock_subreddit("fitness", "Fitness", "General fitness, workouts, and health.")
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
        if "running" in subs or "fitness" in subs:
            fitness_cluster = cluster

    # Verify that HDBSCAN successfully separated Tech from Fitness based on our mock text
    assert tech_cluster is not None, "Tech cluster was not found."
    assert fitness_cluster is not None, "Fitness cluster was not found."
    
    # The crucial test: They should not be dumped into the same cluster ID (like the -1 misc bucket)
    assert tech_cluster["id"] != fitness_cluster["id"], "Tech and Fitness were merged into the same cluster!"
    
    # Verify the related subs ended up grouped together
    assert "reactjs" in tech_cluster["subreddits"]
    assert "python" in tech_cluster["subreddits"]
    assert "javascript" in tech_cluster["subreddits"]
    assert "programming" in tech_cluster["subreddits"]
    assert "running" in fitness_cluster["subreddits"]
    assert "fitness" in fitness_cluster["subreddits"]
    assert "bodyweightfitness" in fitness_cluster["subreddits"]
    assert "weightlifting" in fitness_cluster["subreddits"]