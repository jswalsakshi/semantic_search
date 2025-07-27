import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from pathlib import Path
from typing import Dict, Any
import faiss

class LightweightSearchEngine:
    def __init__(self):
        self.df = None
        self.embeddings = None
        self.index = None
        self.model = None
        self._load_data()
    
    def _load_data(self):
        try:
            # Try enhanced dataset first (PRIORITY FIX)
            if os.path.exists("enhanced_movies.csv"):
                self.df = pd.read_csv("enhanced_movies.csv")
                print(f"✓ Loaded {len(self.df)} movies from enhanced_movies.csv")
                
                # Load enhanced embeddings
                if os.path.exists("enhanced_movie_embeddings.npy"):
                    self.embeddings = np.load("enhanced_movie_embeddings.npy")
                    print("✓ Loaded enhanced embeddings")
                else:
                    print("⚠️ Enhanced embeddings not found, will generate")
                    
            elif os.path.exists("combined_movies.csv"):
                self.df = pd.read_csv("combined_movies.csv")
                print(f"✓ Loaded {len(self.df)} movies from combined_movies.csv")
            else:
                # Create sample data if no CSV found
                self.df = self._create_sample_data()
                print("✓ Using sample movie data")
            
            # Load lightweight model
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✓ Loaded lightweight semantic model")
                
                # Generate or load embeddings
                self._setup_embeddings()
                
            except Exception as e:
                print(f"⚠️ Model loading failed: {e}")
                self.model = None
                
        except Exception as e:
            print(f"⚠️ Data loading failed: {e}")
            self.df = self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample movie data with proper Bollywood comedies"""
        sample_movies = [
            {"title": "3 Idiots", "overview": "Comedy about engineering students and their hilarious college adventures", "vote_average": 8.4, "source": "Bollywood"},
            {"title": "Hera Pheri", "overview": "Comedy about three friends and their get-rich-quick schemes", "vote_average": 8.2, "source": "Bollywood"},
            {"title": "Andaz Apna Apna", "overview": "Comedy about two friends competing for the same girl", "vote_average": 8.3, "source": "Bollywood"},
            {"title": "Munna Bhai MBBS", "overview": "Comedy drama about a gangster trying to become a doctor", "vote_average": 8.1, "source": "Bollywood"},
            {"title": "Queen", "overview": "Comedy drama about woman's solo honeymoon journey", "vote_average": 8.2, "source": "Bollywood"},
            {"title": "The Dark Knight", "overview": "Batman fights crime in Gotham", "vote_average": 9.0, "source": "Hollywood"},
            {"title": "Inception", "overview": "Dreams within dreams", "vote_average": 8.8, "source": "Hollywood"},
            {"title": "Dangal", "overview": "Wrestling father trains daughters", "vote_average": 8.3, "source": "Bollywood"},
            {"title": "Interstellar", "overview": "Space exploration and time", "vote_average": 8.6, "source": "Hollywood"},
            {"title": "Zindagi Na Milegi Dobara", "overview": "Friends on adventure trip with comedy", "vote_average": 8.1, "source": "Bollywood"}
        ]
        
        df = pd.DataFrame(sample_movies)
        
        # Add missing columns with proper genres
        df['genre_names'] = [
            ['Comedy', 'Drama'], ['Comedy'], ['Comedy'], ['Comedy', 'Drama'], ['Comedy', 'Drama'],
            ['Action', 'Crime'], ['Sci-Fi', 'Thriller'], ['Drama', 'Sports'], ['Sci-Fi', 'Drama'], ['Adventure', 'Comedy']
        ]
        df['directors'] = [
            ['Rajkumar Hirani'], ['Priyadarshan'], ['Rajkumar Santoshi'], ['Rajkumar Hirani'], ['Vikas Bahl'],
            ['Christopher Nolan'], ['Christopher Nolan'], ['Nitesh Tiwari'], ['Christopher Nolan'], ['Zoya Akhtar']
        ]
        df['top_cast'] = [
            ['Aamir Khan'], ['Akshay Kumar'], ['Aamir Khan'], ['Sanjay Dutt'], ['Kangana Ranaut'],
            ['Christian Bale'], ['Leonardo DiCaprio'], ['Aamir Khan'], ['Matthew McConaughey'], ['Hrithik Roshan']
        ]
        
        return df
    
    def _setup_embeddings(self):
        """Setup embeddings with enhanced data priority"""
        if self.model is None or self.df is None:
            return
        
        try:
            # Use enhanced embeddings if available
            if os.path.exists("enhanced_movie_embeddings.npy") and os.path.exists("enhanced_movies.csv"):
                print("✓ Using enhanced embeddings")
                return
            
            # Generate embeddings for current data
            embedding_file = "enhanced_embeddings.npy" if "enhanced_text" in self.df.columns else "lightweight_embeddings.npy"
            
            if os.path.exists(embedding_file):
                self.embeddings = np.load(embedding_file)
                print(f"✓ Loaded existing embeddings from {embedding_file}")
            else:
                print("Generating embeddings...")
                
                # Use enhanced text if available, otherwise create simple text
                if "enhanced_text" in self.df.columns:
                    texts = self.df['enhanced_text'].tolist()
                else:
                    texts = []
                    for _, row in self.df.iterrows():
                        text_parts = [row['title']]
                        if pd.notna(row.get('overview')):
                            text_parts.append(row['overview'])
                        if 'genre_names' in row and row['genre_names']:
                            genres = row['genre_names'] if isinstance(row['genre_names'], list) else []
                            text_parts.append(' '.join(genres))
                        if 'source' in row:
                            text_parts.append(row['source'])
                        texts.append(' '.join(text_parts))
                
                # Generate embeddings in batches
                self.embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
                np.save(embedding_file, self.embeddings)
                print(f"✓ Embeddings generated and saved to {embedding_file}")
            
            # Create FAISS index
            if self.embeddings is not None:
                self.index = faiss.IndexFlatIP(self.embeddings.shape[1])
                self.index.add(self.embeddings.astype(np.float32))
                print("✓ FAISS index created")
                
        except Exception as e:
            print(f"⚠️ Embedding setup failed: {e}")
            self.embeddings = None
            self.index = None

# Global instance
search_engine = LightweightSearchEngine()

def combined_search_with_intent(query: str, top_k: int = 10) -> pd.DataFrame:
    """Main search function with improved filtering"""
    if search_engine.df is None:
        return pd.DataFrame()
    
    # Parse query for source filtering
    query_lower = query.lower()
    source_filter = None
    
    if 'bollywood' in query_lower:
        source_filter = 'Bollywood'
        # Remove bollywood from query for better semantic matching
        query_clean = query_lower.replace('bollywood', '').strip()
    elif 'hollywood' in query_lower:
        source_filter = 'Hollywood'
        query_clean = query_lower.replace('hollywood', '').strip()
    else:
        query_clean = query_lower
    
    # Use semantic search if available
    if search_engine.model is not None and search_engine.index is not None:
        try:
            # Search with cleaned query
            search_query = query_clean if query_clean else query
            query_embedding = search_engine.model.encode([search_query], normalize_embeddings=True)
            
            # Get more results for filtering
            search_k = min(top_k * 3, len(search_engine.df))
            D, I = search_engine.index.search(query_embedding.astype(np.float32), search_k)
            
            results = search_engine.df.iloc[I[0]].copy()
            results['semantic_score'] = D[0]
            
            # Apply source filter
            if source_filter:
                results = results[results['source'] == source_filter]
            
            return results.head(top_k)
            
        except Exception as e:
            print(f"Semantic search error: {e}")
            return _enhanced_keyword_search(query, top_k, source_filter)
    else:
        return _enhanced_keyword_search(query, top_k, source_filter)

def _enhanced_keyword_search(query: str, top_k: int, source_filter: str = None) -> pd.DataFrame:
    """Enhanced keyword search with better Bollywood comedy detection"""
    if search_engine.df is None:
        return pd.DataFrame()
    
    query_lower = query.lower()
    
    # Enhanced keyword mapping
    comedy_keywords = ['funny', 'comedy', 'humor', 'hilarious', 'laugh', 'comic', 'entertaining']
    bollywood_keywords = ['bollywood', 'hindi', 'indian']
    
    matches = []
    for idx, row in search_engine.df.iterrows():
        score = 0
        
        # Source filtering (HIGH PRIORITY)
        if source_filter and row.get('source') != source_filter:
            continue
        
        # Title matching
        title_lower = row['title'].lower()
        for word in query_lower.split():
            if word in title_lower:
                score += 0.5
        
        # Overview matching
        if pd.notna(row.get('overview')):
            overview_lower = row['overview'].lower()
            for word in query_lower.split():
                if word in overview_lower:
                    score += 0.3
        
        # Genre matching (ENHANCED)
        if 'genre_names' in row and row['genre_names']:
            genres = row['genre_names'] if isinstance(row['genre_names'], list) else []
            genre_text = ' '.join(genres).lower()
            
            # Comedy genre boost
            if any(comedy_word in query_lower for comedy_word in comedy_keywords):
                if 'comedy' in genre_text:
                    score += 0.8  # High boost for comedy genre
        
        # Source matching
        if row.get('source'):
            source_lower = row['source'].lower()
            if source_filter and source_lower == source_filter.lower():
                score += 0.4  # Boost for correct source
        
        # Special Bollywood comedy movies boost
        if source_filter == 'Bollywood' and any(comedy in query_lower for comedy in comedy_keywords):
            bollywood_comedies = ['3 idiots', 'hera pheri', 'andaz apna apna', 'munna bhai', 'queen', 'golmaal']
            if any(movie in title_lower for movie in bollywood_comedies):
                score += 1.0  # High boost for known comedies
        
        if score > 0:
            matches.append((idx, score))
    
    # Sort by score and return top results
    matches.sort(key=lambda x: x[1], reverse=True)
    indices = [match[0] for match in matches[:top_k]]
    
    if indices:
        results = search_engine.df.iloc[indices].copy()
        results['semantic_score'] = [match[1] for match in matches[:len(indices)]]
        return results
    else:
        # Fallback: return Bollywood movies if source filter is set
        if source_filter:
            filtered_df = search_engine.df[search_engine.df['source'] == source_filter]
            return filtered_df.head(top_k)
        else:
            return search_engine.df.sample(min(top_k, len(search_engine.df)))

def search_by_source(query: str, source: str = "Bollywood", top_k: int = 10) -> pd.DataFrame:
    """Search by specific source with enhanced filtering"""
    # Force source in query
    enhanced_query = f"{source} {query}"
    results = combined_search_with_intent(enhanced_query, top_k)
    
    # Double-check source filtering
    if not results.empty and 'source' in results.columns:
        results = results[results['source'] == source]
    
    return results.head(top_k)

def get_recommendations_by_source(source: str = "Bollywood", genre: str = None, top_k: int = 10) -> pd.DataFrame:
    """Get recommendations by source and genre"""
    if search_engine.df is None:
        return pd.DataFrame()
    
    # Filter by source first
    filtered_df = search_engine.df[search_engine.df['source'] == source].copy()
    
    # Then filter by genre if specified
    if genre:
        filtered_df = filtered_df[filtered_df['genre_names'].apply(
            lambda x: any(genre.lower() in g.lower() for g in x) if isinstance(x, list) else False
        )]
    
    return filtered_df.nlargest(min(top_k, len(filtered_df)), 'vote_average')

def get_search_analytics(query: str) -> Dict[str, Any]:
    """Enhanced search analytics"""
    query_lower = query.lower()
    
    # Enhanced intent detection
    if any(word in query_lower for word in ['like', 'similar']):
        intent = 'find similar movies'
    elif any(word in query_lower for word in ['funny', 'comedy', 'humor']):
        intent = 'search for comedy movies'
    elif any(word in query_lower for word in ['actor', 'starring']):
        intent = 'search by actor or cast'
    elif any(word in query_lower for word in ['director', 'directed']):
        intent = 'search by director'
    else:
        intent = 'search by plot or story'
    
    # Enhanced entity extraction
    entities = {
        'persons': [],
        'movies': [],
        'genres': [],
        'years': [],
        'sources': []
    }
    
    # Genre detection
    if any(word in query_lower for word in ['funny', 'comedy', 'humor']):
        entities['genres'].append('comedy')
    
    # Source detection
    if 'bollywood' in query_lower:
        entities['sources'].append('Bollywood')
    elif 'hollywood' in query_lower:
        entities['sources'].append('Hollywood')
    
    return {
        'intent': {
            'primary_intent': intent,
            'confidence': 0.9,
            'all_intents': {intent: 0.9, 'general search': 0.1}
        },
        'entities': entities,
        'processed_query': query
    }