import React, { useState, useEffect } from 'react';
import {
    Network,
    LogIn,
    Loader2,
    CheckCircle2,
    FolderTree,
    Settings2,
    ArrowRight,
    ShieldCheck,
    AlertCircle
} from 'lucide-react';

export default function App() {
    // App states: 'login' | 'authorizing' | 'clustering' | 'review' | 'saving' | 'success' | 'error'
    const [appState, setAppState] = useState('login');
    const [clusters, setClusters] = useState([]);
    const [refreshToken, setRefreshToken] = useState(null);
    const [errorMessage, setErrorMessage] = useState("");

    // Reddit OAuth Settings
    // Ensure this matches the Client ID from your Reddit Developer Portal
    const CLIENT_ID = "YOUR_REDDIT_CLIENT_ID";
    // Ensure this matches the Client Secret from your Reddit Developer Portal
    const CLIENT_SECRET = "YOUR_REDDIT_CLIENT_SECRET";
    
    // Ensure this matches the Redirect URI from your Reddit Developer Portal
    const REDIRECT_URI = "http://localhost:3000";
    const BACKEND_URL = "http://localhost:8000";

    useEffect(() => {
        // Check if we are returning from Reddit with an OAuth code
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const error = urlParams.get('error');

        if (error) {
            setErrorMessage("Reddit authorization failed or was denied.");
            setAppState('error');
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
        } else if (code) {
            // Send the code to the backend to run the clustering
            setAppState('clustering');
            window.history.replaceState({}, document.title, window.location.pathname);
            processRedditCode(code);
        }
    }, []);

    const processRedditCode = async (code) => {
        try {
            const response = await fetch(`${BACKEND_URL}/api/cluster`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code })
            });

            if (!response.ok) {
                throw new Error("Failed to process subreddits on the server.");
            }

            const data = await response.json();
            setRefreshToken(data.refresh_token);
            setClusters(data.clusters);
            setAppState('review');
        } catch (err) {
            setErrorMessage(err.message);
            setAppState('error');
        }
    };

    const handleLoginClick = () => {
        setAppState('authorizing');
        // Generate standard Reddit OAuth URL
        const state = Math.random().toString(36).substring(7);
        
        // Define the required scopes for the application
        // The scopes needed are: "mysubreddits" to read the user's subscribed subreddits, "read" to read subreddit content, and "subscribe" to create custom feeds.
        const scope = "mysubreddits read subscribe";
        const authUrl = `https://www.reddit.com/api/v1/authorize?client_id=${CLIENT_ID}&response_type=code&state=${state}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&duration=permanent&scope=${encodeURIComponent(scope)}`;

        // Redirect browser to Reddit
        window.location.href = authUrl;
    };

    const handleSaveToReddit = async () => {
        setAppState('saving');
        try {
            const response = await fetch(`${BACKEND_URL}/api/save-feeds`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    refresh_token: refreshToken,
                    clusters: clusters
                })
            });

            if (!response.ok) throw new Error("Failed to save custom feeds.");

            setAppState('success');
        } catch (err) {
            setErrorMessage(err.message);
            setAppState('error');
        }
    };

    const renderLogin = () => (
        <div className="text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="space-y-4">
                <div className="mx-auto w-20 h-20 bg-orange-100 rounded-2xl flex items-center justify-center mb-6 shadow-sm border border-orange-200">
                    <Network className="w-10 h-10 text-orange-500" />
                </div>
                <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">
                    Unclutter your Reddit feed.
                </h1>
                <p className="text-lg text-slate-600 max-w-lg mx-auto leading-relaxed">
                    Our AI reads the context of your subscribed subreddits and automatically groups them into hyper-focused Custom Feeds.
                </p>
            </div>

            <div className="pt-8">
                <button
                    onClick={handleLoginClick}
                    className="group relative inline-flex items-center justify-center px-8 py-4 font-bold text-white transition-all duration-200 bg-orange-600 font-pj rounded-xl hover:bg-orange-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-600 shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                >
                    <LogIn className="w-5 h-5 mr-3" />
                    Connect with Reddit
                    <ArrowRight className="w-5 h-5 ml-3 opacity-0 group-hover:opacity-100 transition-opacity -translate-x-2 group-hover:translate-x-0 duration-200" />
                </button>
                <div className="mt-6 flex items-center justify-center space-x-2 text-sm text-slate-500">
                    <ShieldCheck className="w-4 h-4 text-emerald-500" />
                    <span>We only ask for permission to read subs and create feeds.</span>
                </div>
            </div>
        </div>
    );

    const renderProcessing = () => (
        <div className="text-center space-y-8 py-12 animate-in fade-in duration-500">
            <div className="relative">
                <div className="absolute inset-0 flex items-center justify-center opacity-20">
                    <Loader2 className="w-32 h-32 text-orange-500 animate-spin" style={{ animationDuration: '3s' }} />
                </div>
                <div className="relative mx-auto w-24 h-24 bg-white rounded-full flex items-center justify-center shadow-lg border border-slate-100 z-10">
                    {appState === 'clustering' ? (
                        <Settings2 className="w-10 h-10 text-blue-500 animate-spin" style={{ animationDuration: '4s' }} />
                    ) : (
                        <Network className="w-10 h-10 text-orange-500 animate-pulse" />
                    )}
                </div>
            </div>

            <div className="space-y-2">
                <h2 className="text-2xl font-bold text-slate-900">
                    {appState === 'authorizing' ? "Redirecting to Reddit..." :
                        appState === 'clustering' ? "Running AI Clustering on Backend..." :
                            "Saving Feeds to Reddit..."}
                </h2>
                <p className="text-slate-500">
                    {appState === 'authorizing' ? "Please authorize the application." :
                        appState === 'clustering' ? "Fetching your subs and generating vector embeddings. This takes a moment." :
                            "Creating Custom Feeds on your account."}
                </p>
            </div>
        </div>
    );

    const renderReview = () => (
        <div className="w-full max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="text-center space-y-2">
                <h2 className="text-3xl font-bold text-slate-900">Review your new feeds</h2>
                <p className="text-slate-600">We grouped your subreddits into these custom feeds. You can save them directly to your Reddit account.</p>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                {clusters.map(cluster => (
                    <div key={cluster.id} className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col max-h-96">
                        <div className="flex items-center space-x-3 mb-4 shrink-0">
                            <span className="text-2xl">{cluster.icon}</span>
                            <h3 className="font-bold text-slate-900 leading-tight">{cluster.name}</h3>
                        </div>
                        <div className="space-y-2 overflow-y-auto pr-2">
                            {cluster.subreddits.map(sub => (
                                <div key={sub} className="flex items-center text-sm text-slate-600 bg-slate-50 px-3 py-2 rounded-lg border border-slate-100">
                                    <span className="text-slate-400 mr-2">r/</span>
                                    <span className="font-medium truncate">{sub}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            <div className="flex justify-center pt-6">
                <button
                    onClick={handleSaveToReddit}
                    className="inline-flex items-center px-8 py-4 font-bold text-white bg-slate-900 rounded-xl hover:bg-slate-800 transition-colors shadow-lg"
                >
                    <FolderTree className="w-5 h-5 mr-3" />
                    Create Feeds on Reddit
                </button>
            </div>
        </div>
    );

    const renderSuccess = () => (
        <div className="text-center space-y-6 animate-in zoom-in-95 duration-500">
            <div className="mx-auto w-24 h-24 bg-emerald-100 rounded-full flex items-center justify-center mb-8">
                <CheckCircle2 className="w-12 h-12 text-emerald-500" />
            </div>
            <h2 className="text-3xl font-bold text-slate-900">All Done!</h2>
            <p className="text-slate-600 max-w-md mx-auto">
                Your new custom feeds have been successfully created. Check the left sidebar on your Reddit homepage to see them.
            </p>
            <div className="pt-6">
                <button
                    onClick={() => { setAppState('login'); setClusters([]); }}
                    className="text-slate-500 hover:text-slate-900 font-medium transition-colors"
                >
                    Start Over
                </button>
            </div>
        </div>
    );

    const renderError = () => (
        <div className="text-center space-y-6 animate-in zoom-in-95 duration-500">
            <div className="mx-auto w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mb-8">
                <AlertCircle className="w-12 h-12 text-red-500" />
            </div>
            <h2 className="text-3xl font-bold text-slate-900">Something went wrong</h2>
            <p className="text-slate-600 max-w-md mx-auto bg-red-50 p-4 rounded-lg border border-red-100">
                {errorMessage}
            </p>
            <div className="pt-6">
                <button
                    onClick={() => setAppState('login')}
                    className="inline-flex items-center px-6 py-3 font-bold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 transition-colors"
                >
                    Try Again
                </button>
            </div>
        </div>
    );

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col">
            <header className="px-6 py-4 border-b border-slate-200 bg-white shadow-sm flex items-center shrink-0">
                <div className="flex items-center space-x-2">
                    <Network className="w-6 h-6 text-orange-500" />
                    <span className="font-bold text-lg tracking-tight">Reddit Subs to Custom Feeds</span>
                </div>
            </header>

            <main className="flex-1 flex flex-col items-center justify-center p-6 md:p-12">
                {appState === 'login' && renderLogin()}
                {['authorizing', 'clustering', 'saving'].includes(appState) && renderProcessing()}
                {appState === 'review' && renderReview()}
                {appState === 'success' && renderSuccess()}
                {appState === 'error' && renderError()}
            </main>
        </div>
    );
}