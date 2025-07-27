Semantic Search POC using Sentence-BERT & FAISS
This project demonstrates a Semantic Search approach using Sentence-BERT embeddings and FAISS for efficient similarity search. A simple Streamlit UI is provided for testing queries against sample content (like movies).

✅ Overview
Traditional keyword-based search often fails for queries like:

Synonyms: "romantic comedy" vs "rom-com"

Intent: "movies like Dangal"

This POC uses sentence embeddings to capture the meaning of queries and content, enabling context-aware search results.

✅ Features
Semantic Search: Finds relevant results using embeddings, not just keywords.

Intent Handling: Supports queries like "movies like XYZ".

FAISS Indexing: Fast similarity search over large datasets.

Streamlit UI: Simple interface for testing queries.

✅ Tech Stack
Python 3.9+

Sentence-BERT (sentence-transformers)

FAISS

Streamlit (UI)

Pandas / Numpy

✅ How It Works
Generate embeddings for all content titles/descriptions using Sentence-BERT.

Store embeddings in a FAISS index for fast retrieval.

On user query:

Convert query to embedding.

Retrieve top-k similar items from FAISS.

Display results in Streamlit UI.

✅ Installation
Clone the repository:

bash
Copy
Edit
git clone https://github.com/jswalsakshi/semantic_search.git
cd semantic_search
Create a virtual environment:

bash
Copy
Edit
python3 -m venv venv
source venv/bin/activate
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
✅ Run the App
bash
Copy
Edit
streamlit run app.py
✅ Example Queries
rom com movies

movies like Dangal

funny superhero movies

✅ Screenshots
(Attach your Before vs After screenshots here)

Current Search	Semantic Search (POC)

✅ Future Scope
Multilingual query support.

Personalized ranking using user history.

Integration with Hotstar BFF architecture.

Deploy as an API service.

✅ Contributing
Feel free to fork this repo and enhance the POC!

✅ License
MIT License.

