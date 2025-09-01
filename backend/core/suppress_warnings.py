"""
Suppress third-party library warnings that we cannot control
This module should be imported as early as possible in the application
"""
import warnings
import sys

def suppress_third_party_warnings():
    """
    Suppress warnings from third-party libraries that use deprecated patterns
    but are outside our control to fix directly.
    """
    
    # Tweepy library - uses invalid escape sequences in docstrings and deprecated modules
    # This is a known issue with Tweepy and Python 3.12+
    warnings.filterwarnings("ignore", category=SyntaxWarning, module="tweepy")
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="tweepy")
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="tweepy.api")
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="tweepy.auth")
    warnings.filterwarnings("ignore", message=".*imghdr.*deprecated.*")
    warnings.filterwarnings("ignore", message=".*OAuthHandler.*deprecated.*")
    warnings.filterwarnings("ignore", message=".*'imghdr' is deprecated.*")
    
    # pysbd library - uses regex patterns with deprecated escape sequences
    warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")
    warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd.segmenter")
    warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd.lang.arabic")
    warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd.lang.persian")
    
    # Remove ChromaDB warnings (not used in this project - FAISS is used instead)
    # Keeping generic Pydantic warnings for other third-party libraries
    warnings.filterwarnings("ignore", message=".*model_fields.*attribute.*deprecated.*")
    warnings.filterwarnings("ignore", message=".*PydanticDeprecatedSince211.*")
    
    # Pydantic v2 migration warnings - now mostly resolved by our fixes
    # Keeping minimal suppression for any remaining third-party library warnings
    warnings.filterwarnings("ignore", message="Valid config keys have changed in V2")
    
    # SQLAlchemy 2.0 migration warnings
    warnings.filterwarnings("ignore", message=".*declarative_base.*deprecated.*")
    warnings.filterwarnings("ignore", message=".*MovedIn20Warning.*")
    
    # Billiard/Celery warnings about forking in multi-threaded processes
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="billiard")
    warnings.filterwarnings("ignore", message=".*multi-threaded.*fork.*deadlocks.*")
    
    # bcrypt version reading errors - library compatibility issue
    warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")
    warnings.filterwarnings("ignore", message=".*bcrypt.*has no attribute '__about__'.*")
    
    # FAISS availability warnings - shown only when vector store is used
    warnings.filterwarnings("ignore", message=".*FAISS not available.*")
    warnings.filterwarnings("ignore", message=".*faiss-cpu for better performance.*")
    
    # Suppress import-time SyntaxWarnings if running Python 3.12+
    if sys.version_info >= (3, 12):
        warnings.filterwarnings("ignore", category=SyntaxWarning)
        # Re-enable our own SyntaxWarnings
        warnings.filterwarnings("default", category=SyntaxWarning, module="backend")
        warnings.filterwarnings("default", category=SyntaxWarning, module="app")

# Call this function when module is imported
suppress_third_party_warnings()