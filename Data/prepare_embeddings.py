import pandas as pd
import numpy as np
import json
from pathlib import Path
import os

# Change to project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)

def get_movie_keywords(title, overview, genres, directors, cast):
    """Generate rich keywords and context for movies"""
    keywords = []
    
    # Title-based keywords
    title_lower = title.lower()
    
    # Sports movies keywords
    sports_keywords = {
        'dangal': ['wrestling', 'biography', 'sports drama', 'father daughter', 'Olympic wrestling', 'biographical sports'],
        'bhaag milkha bhaag': ['running', 'athletics', 'biography', 'sports drama', 'Olympic runner'],
        'chak de india': ['hockey', 'women sports', 'national team', 'coach', 'sports drama'],
        'mary kom': ['boxing', 'biography', 'women sports', 'Olympic boxing'],
        'sultan': ['wrestling', 'sports drama', 'mixed martial arts'],
        'rocky': ['boxing', 'underdog', 'sports drama', 'training montage'],
        'the pursuit of happyness': ['biography', 'inspirational', 'father son', 'struggle'],
        'ford v ferrari': ['racing', 'biography', 'automotive', 'sports drama']
    }
    
    # Biographical movie indicators
    biographical_indicators = [
        'biography', 'biopic', 'biographical', 'based on true story', 
        'real life', 'true events', 'historical figure'
    ]
    
    # Sports categories
    sports_categories = {
        'wrestling': ['wrestling', 'dangal', 'sultan', 'grappling'],
        'boxing': ['boxing', 'mary kom', 'rocky', 'fighter'],
        'running': ['running', 'milkha', 'athletics', 'track'],
        'hockey': ['hockey', 'chak de', 'field hockey'],
        'cricket': ['cricket', 'bat', 'wicket', 'bowling'],
        'football': ['football', 'soccer', 'goal']
    }
    
    # Add specific keywords for known movies
    for movie, movie_keywords in sports_keywords.items():
        if movie in title_lower:
            keywords.extend(movie_keywords)
    
    # Add biographical context
    if overview and any(indicator in overview.lower() for indicator in biographical_indicators):
        keywords.extend(['biographical', 'true story', 'real person', 'inspiring'])
    
    # Add sports context
    for sport, sport_keywords in sports_categories.items():
        if any(keyword in title_lower or (overview and keyword in overview.lower()) for keyword in sport_keywords):
            keywords.extend([f'{sport} movie', f'{sport} drama', f'{sport} sports'])
    
    # Family drama indicators
    family_keywords = ['father', 'daughter', 'son', 'family', 'parent', 'child']
    if overview and any(keyword in overview.lower() for keyword in family_keywords):
        keywords.extend(['family drama', 'family relationships', 'emotional'])
    
    # Add genre-specific context
    if genres:
        genre_context = {
            'Drama': ['emotional', 'character driven', 'serious'],
            'Sports': ['competition', 'training', 'achievement', 'athletic'],
            'Biography': ['real person', 'life story', 'historical'],
            'Action': ['intense', 'thrilling', 'fast paced'],
            'Comedy': ['funny', 'humorous', 'entertaining'],
            'Romance': ['love story', 'romantic', 'relationship']
        }
        
        for genre in genres:
            if genre in genre_context:
                keywords.extend(genre_context[genre])
    
    return list(set(keywords))  # Remove duplicates

def create_enhanced_text_v2(row):
    """Create much richer text representation for better embeddings"""
    text_parts = []
    
    # Title with emphasis
    text_parts.append(f"Movie: {row['title']}")
    
    # Enhanced overview
    if pd.notna(row.get('overview')):
        text_parts.append(f"Story: {row['overview']}")
    
    # Rich genre description
    if 'genre_names' in row and row['genre_names'] and len(row['genre_names']) > 0:
        genres = row['genre_names'] if isinstance(row['genre_names'], list) else [row['genre_names']]
        
        # Create detailed genre description
        genre_descriptions = {
            'Drama': 'emotional drama with deep character development',
            'Sports': 'sports-centered story with athletic competition and training',
            'Biography': 'biographical film based on real person and true events',
            'Action': 'action-packed with intense sequences',
            'Comedy': 'comedy film with humor and entertainment',
            'Romance': 'romantic story about love and relationships',
            'Thriller': 'suspenseful thriller with tension',
            'Horror': 'horror film with scary elements'
        }
        
        detailed_genres = []
        for genre in genres:
            if genre in genre_descriptions:
                detailed_genres.append(genre_descriptions[genre])
            else:
                detailed_genres.append(f'{genre.lower()} film')
        
        text_parts.append(f"Genre: {', '.join(detailed_genres)}")
    
    # Enhanced cast information (safe access)
    if 'top_cast' in row and row['top_cast'] and len(row['top_cast']) > 0:
        cast = row['top_cast'] if isinstance(row['top_cast'], list) else [row['top_cast']]
        text_parts.append(f"Features actors: {', '.join(str(c) for c in cast[:5])}")
    
    # Enhanced director information (safe access)
    if 'directors' in row and row['directors'] and len(row['directors']) > 0:
        directors = row['directors'] if isinstance(row['directors'], list) else [row['directors']]
        text_parts.append(f"Filmmaker: {', '.join(str(d) for d in directors)}")
    
    # Source with cultural context
    source_context = {
        'Bollywood': 'Indian Hindi cinema Bollywood production',
        'Hollywood': 'American Hollywood production'
    }
    source_desc = source_context.get(row.get('source', ''), row.get('source', ''))
    text_parts.append(f"Origin: {source_desc}")
    
    # Generate contextual keywords
    keywords = get_movie_keywords(
        row['title'], 
        row.get('overview', ''),
        row.get('genre_names', []),
        row.get('directors', []),
        row.get('top_cast', [])
    )
    
    if keywords:
        text_parts.append(f"Keywords: {', '.join(keywords[:10])}")  # Limit to 10 keywords
    
    # Release context
    if pd.notna(row.get('release_date')):
        try:
            year = str(row['release_date'])[:4]
            text_parts.append(f"Released: {year}")
        except:
            pass
    
    # Quality indicator
    if pd.notna(row.get('vote_average')):
        rating = row['vote_average']
        if rating >= 8.0:
            text_parts.append("Quality: highly rated acclaimed film")
        elif rating >= 7.0:
            text_parts.append("Quality: well-received good film")
    
    return " | ".join(text_parts)

def standardize_genres(genre_text):
    """Convert different genre formats to a standardized list"""
    if pd.isna(genre_text):
        return []
    
    if isinstance(genre_text, str) and genre_text.startswith('[{'):
        try:
            genre_data = json.loads(genre_text)
            return [item['name'] for item in genre_data]
        except:
            return []
    
    return [genre_text] if isinstance(genre_text, str) else []

def extract_directors_from_crew(crew_text):
    """Extract directors from crew JSON string"""
    if pd.isna(crew_text):
        return []
    
    try:
        crew_data = json.loads(crew_text)
        directors = [person['name'] for person in crew_data if person.get('job') == 'Director']
        return directors[:3]  # Limit to 3 directors
    except:
        return []

def extract_cast_from_cast(cast_text):
    """Extract main cast from cast JSON string"""
    if pd.isna(cast_text):
        return []
    
    try:
        cast_data = json.loads(cast_text)
        main_cast = [person['name'] for person in cast_data[:5]]  # Top 5 cast members
        return main_cast
    except:
        return []

def combine_datasets_enhanced():
    """Enhanced dataset combination with better text representations"""
    
    # Load datasets
    print("Loading datasets...")
    movies_df = pd.read_csv("movies.csv")
    bollywood_df = pd.read_csv("bollywood_movies.csv")
    
    print(f"Hollywood movies: {len(movies_df)}")
    print(f"Bollywood movies: {len(bollywood_df)}")
    
    # Check what columns exist in movies_df
    print(f"Hollywood columns: {list(movies_df.columns)}")
    print(f"Bollywood columns: {list(bollywood_df.columns)}")
    
    # Enhanced Bollywood processing with better context
    bollywood_processed = pd.DataFrame()
    bollywood_processed['title'] = bollywood_df['Movie_Name']
    
    # Create much better overviews for Bollywood movies
    def create_bollywood_overview(row):
        genre = row['Genre'].lower() if pd.notna(row['Genre']) else 'drama'
        star = row['Lead_Star'] if pd.notna(row['Lead_Star']) else 'Unknown'
        director = row['Director'] if pd.notna(row['Director']) else 'Unknown'
        
        # Special cases for known movies
        movie_name = row['Movie_Name'].lower()
        
        if 'dangal' in movie_name:
            return "Biographical sports drama about wrestling coach Mahavir Singh training his daughters to become world-class wrestlers, based on true story of Geeta and Babita Phogat"
        elif any(sport in movie_name for sport in ['milkha', 'bhaag']):
            return "Biographical sports drama about Indian athlete and Olympic runner, inspiring true story of determination and achievement"
        elif 'mary kom' in movie_name:
            return "Biographical sports drama about Indian boxer Mary Kom, women's boxing champion and Olympic medalist"
        elif '3 idiots' in movie_name:
            return "Comedy drama about three engineering students and their hilarious college adventures, exploring friendship and following dreams"
        elif 'hera pheri' in movie_name:
            return "Comedy about three friends and their hilarious get-rich-quick schemes, classic Bollywood humor"
        elif 'munna bhai' in movie_name:
            return "Comedy drama about a gangster trying to become a doctor, heartwarming story with humor"
        elif 'queen' in movie_name:
            return "Comedy drama about independent woman's solo honeymoon journey, empowering and funny"
        
        # Genre-specific templates
        if 'comedy' in genre:
            return f"Comedy entertainment film starring {star}, directed by {director}, providing humor and lighthearted storytelling"
        elif 'action' in genre:
            return f"Action-packed film starring {star}, directed by {director}, featuring intense sequences and thrilling entertainment"
        else:
            return f"Emotional {genre} film starring {star}, directed by {director}, exploring deep human relationships and personal growth"
    
    bollywood_processed['overview'] = bollywood_df.apply(create_bollywood_overview, axis=1)
    
    # Rest of the processing...
    bollywood_processed['release_date'] = bollywood_df['Release_Period'].apply(lambda x: f"2010-01-01" if x == 'Holiday' else "2010-06-01")
    bollywood_processed['runtime'] = 150
    bollywood_processed['vote_average'] = np.random.uniform(6.5, 8.5, len(bollywood_df))
    bollywood_processed['vote_count'] = bollywood_df['Revenue(INR)'] / 10000
    
    # Enhanced genre mapping
    def enhanced_genre_mapping(genre_text):
        if pd.isna(genre_text):
            return ['Drama']
        
        genre_lower = genre_text.lower()
        enhanced_mapping = {
            'drama': ['Drama', 'Family'],
            'sports': ['Sports', 'Drama', 'Biography'],
            'action': ['Action', 'Thriller'],
            'comedy': ['Comedy', 'Family'],
            'romance': ['Romance', 'Drama'],
            'thriller': ['Thriller', 'Drama'],
            'masala': ['Action', 'Comedy', 'Drama']
        }
        
        return enhanced_mapping.get(genre_lower, [genre_text.title()])
    
    bollywood_processed['genre_names'] = bollywood_df['Genre'].apply(enhanced_genre_mapping)
    bollywood_processed['source'] = 'Bollywood'
    bollywood_processed['directors'] = bollywood_df['Director'].apply(lambda x: [x] if pd.notna(x) else [])
    bollywood_processed['top_cast'] = bollywood_df['Lead_Star'].apply(lambda x: [x] if pd.notna(x) else [])
    
    # Process Hollywood data - FIXED to handle missing columns
    hollywood_processed = movies_df.copy()
    hollywood_processed['source'] = 'Hollywood'
    hollywood_processed['genre_names'] = hollywood_processed['genres'].apply(standardize_genres)
    
    # Fix overview column
    if 'overview' not in hollywood_processed.columns:
        hollywood_processed['overview'] = 'No description available'
    else:
        hollywood_processed['overview'] = hollywood_processed['overview'].fillna('No description available')
    
    # Add missing directors column
    if 'directors' not in hollywood_processed.columns:
        if 'crew' in hollywood_processed.columns:
            hollywood_processed['directors'] = hollywood_processed['crew'].apply(extract_directors_from_crew)
        else:
            hollywood_processed['directors'] = [[] for _ in range(len(hollywood_processed))]
    
    # Add missing top_cast column
    if 'top_cast' not in hollywood_processed.columns:
        if 'cast' in hollywood_processed.columns:
            hollywood_processed['top_cast'] = hollywood_processed['cast'].apply(extract_cast_from_cast)
        else:
            hollywood_processed['top_cast'] = [[] for _ in range(len(hollywood_processed))]
    
    # Ensure all required columns exist
    required_columns = ['title', 'overview', 'release_date', 'runtime', 'vote_average', 'vote_count', 'genre_names', 'directors', 'top_cast', 'source']
    
    for col in required_columns:
        if col not in hollywood_processed.columns:
            if col == 'release_date':
                hollywood_processed[col] = '2000-01-01'
            elif col == 'runtime':
                hollywood_processed[col] = 120
            elif col == 'vote_average':
                hollywood_processed[col] = 7.0
            elif col == 'vote_count':
                hollywood_processed[col] = 1000
            else:
                hollywood_processed[col] = ''
    
    # Select only common columns that exist in both datasets
    common_columns = [
        'title', 'overview', 'release_date', 'runtime', 'vote_average', 'vote_count',
        'genre_names', 'directors', 'top_cast', 'source'
    ]
    
    # Combine datasets
    print("Combining datasets...")
    combined_df = pd.concat([
        hollywood_processed[common_columns],
        bollywood_processed[common_columns]
    ], ignore_index=True)
    
    # Use enhanced text creation
    print("Creating enhanced text...")
    combined_df['enhanced_text'] = combined_df.apply(create_enhanced_text_v2, axis=1)
    
    # Clean the dataset
    combined_df = combined_df.dropna(subset=['title'])
    combined_df = combined_df[combined_df['title'].str.len() > 0]
    
    print(f"Enhanced combined dataset: {len(combined_df)} movies")
    return combined_df

if __name__ == "__main__":
    try:
        # Generate enhanced embeddings
        combined_df = combine_datasets_enhanced()
        
        print("\nGenerating enhanced embeddings...")
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(combined_df['enhanced_text'].tolist(), normalize_embeddings=True, show_progress_bar=True)
        
        # Save enhanced dataset and embeddings
        np.save('enhanced_movie_embeddings.npy', embeddings)
        combined_df.to_csv('enhanced_movies.csv', index=False)
        
        print(f"✓ Enhanced embeddings generated! Shape: {embeddings.shape}")
        print(f"✓ Enhanced dataset saved: {len(combined_df)} movies")
        
        # Show sample enhanced text for comedy movies
        print("\nSample enhanced text for comedy movies:")
        comedy_movies = combined_df[combined_df['enhanced_text'].str.contains('comedy|funny|humor', case=False, na=False)]
        for _, row in comedy_movies.head(3).iterrows():
            print(f"\n{row['title']} ({row['source']}):")
            print(f"{row['enhanced_text'][:200]}...")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()