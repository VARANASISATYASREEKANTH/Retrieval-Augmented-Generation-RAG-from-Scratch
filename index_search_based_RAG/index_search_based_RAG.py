import os
import deeplake
from deeplake.core.vectorstore import VectorStore
from sentence_transformers import SentenceTransformer

# 1. Path Configuration
# Using raw string for Windows compatibility
vector_store_path = r"C:\my_projects\RAG_construction_from_scrarch\index_search_based_RAG\vector_store_local"

# 2. Initialize Schema (One-time setup)
# Overwrite=True ensures we start fresh with the correct id and embedding tensors
# 1. Initialize Schema with singular 'embedding'
ds = deeplake.empty(vector_store_path, overwrite=True)
ds.create_tensor('embedding', htype='embedding', dtype='float32') # Fixed name
ds.create_tensor('text', htype='text')
ds.create_tensor('id', htype='text')
ds.create_tensor('metadata', htype='json')

print("Dataset initialized correctly.")

print("Dataset initialized with all required tensors.")

# 3. Define Local Embedding Model
# We load the model once here to avoid reloading it inside functions
print("Loading sentence-transformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

def embedding_function(texts):
    if isinstance(texts, str): 
        texts = [texts]
    embeddings = model.encode(texts)
    return embeddings.tolist()

# 4. Load VectorStore
vector_store = VectorStore(path=vector_store_path)

# 5. POPULATE THE DATASET
# FIX: Use 'embedding_data' so Deep Lake knows what to pass to the embedding_function
documents = [
    "NASA's Artemis program aims to return humans to the Moon by 2026.",
    "SpaceX is developing Starship to enable colonization and exploration of Mars.",
    "The Lunar Gateway is a planned space station in orbit around the Moon.",
    "Mars has a thin atmosphere composed mostly of carbon dioxide."
]

print("Adding documents to vector store...")
vector_store.add(
    text=documents,
    embedding_data=documents,  # <--- THIS FIXES THE VALUEERROR
    id=[f"id_{i}" for i in range(len(documents))],
    metadata=[{"source": "space_news_db"} for _ in documents],
    embedding_function=embedding_function
)
print(f"Successfully added {len(documents)} documents.")

# 6. Search Logic
def search_query(prompt):
    # k=1 retrieves the single most relevant chunk
    return vector_store.search(
        embedding_data=prompt, 
        embedding_function=embedding_function,
        k=1 
    )

user_prompt = "Tell me about space exploration on the Moon and Mars."
search_results = search_query(user_prompt)

# 7. Output Formatting
def wrap_text(text, width=80):
    import textwrap
    return textwrap.fill(text, width=width)

if len(search_results['score']) > 0:
    top_score = search_results['score'][0]
    top_text = search_results['text'][0].strip()
    top_source = search_results['metadata'][0].get('source', 'N/A')

    print("\n" + "="*40)
    print("TOP SEARCH RESULT")
    print("="*40)
    print(f"Score:  {top_score:.4f}")
    print(f"Source: {top_source}")
    print(f"Text:   \n{wrap_text(top_text)}")
    
    # Augmented prompt for LLM phase
    augmented_input = f"Context: {top_text}\n\nQuestion: {user_prompt}"
    print("\n" + "="*40)
    print("AUGMENTED PROMPT FOR LLM")
    print("="*40)
    print(augmented_input)
else:
    print("No results found. Ensure your 'documents' list has content.")
    
    
    
    
#################Generation and Output with Open-AI Reasoning models#################################
# Note: The Augmented input('augmented_input') can be passed to any LLM, to get the generated text