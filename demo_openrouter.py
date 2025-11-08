"""
Demo script for OpenRouter-powered Echoes backend.

Prerequisites:
1. Install dependencies: pip install -r requirements.txt
2. Configure .env with your OpenRouter API key
3. Start server: uvicorn api.main:app --reload --port 8000
4. Run: python demo_openrouter.py
"""
import requests
import json
import time
from typing import List


BASE_URL = "http://localhost:8000"


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_json(data):
    """Pretty print JSON."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def check_health():
    """Test health endpoint."""
    print_header("1. HEALTH CHECK")
    
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    
    print(f"Status: {data['status']}")
    print(f"Version: {data['version']}")
    print(f"Model: {data['model']}")
    print(f"LLM Enabled: {data['llm_enabled']}")
    print(f"Cache Enabled: {data['cache_enabled']}")
    
    return data['status'] == 'ok'


def test_generate_evolution(word: str, eras: List[str]):
    """Test word evolution generation."""
    print_header(f"2. GENERATE EVOLUTION: '{word.upper()}'")
    
    print(f"Word: {word}")
    print(f"Eras: {', '.join(eras)}")
    print(f"\nGenerating with OpenRouter (this may take 10-30 seconds)...")
    
    start = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate-evolution",
            json={
                "word": word,
                "eras": eras,
                "num_examples": 5
            },
            timeout=90
        )
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success! (took {elapsed:.1f}s)")
            print(f"Model: {data['model']}")
            print(f"Total examples: {data['total_examples']}")
            
            print("\nEvolution across time:")
            for era in eras:
                if era in data['evolution']:
                    print(f"\n  📅 {era}:")
                    for i, example in enumerate(data['evolution'][era], 1):
                        print(f"     {i}. {example}")
                else:
                    print(f"\n  📅 {era}: No data")
            
            return data
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            return None
    
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out after {elapsed:.1f}s")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def test_build_embeddings(word: str, eras: List[str]):
    """Test complete pipeline."""
    print_header(f"3. BUILD EMBEDDINGS: '{word.upper()}'")
    
    print(f"Building complete embeddings...")
    print(f"This will: 1) Generate evolution data, 2) Create embeddings, 3) Save to disk")
    print(f"\nThis may take 15-45 seconds...")
    
    start = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/build-embeddings",
            json={
                "word": word,
                "eras": eras,
                "num_examples": 5
            },
            timeout=120
        )
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success! (took {elapsed:.1f}s)")
            print(f"Total items created: {data['total_items']}")
            print(f"LLM model: {data['llm_model']}")
            print(f"Embedding model: {data['embedding_model']}")
            print(f"\nFiles created:")
            for file in data['embeddings_files']:
                print(f"  📄 {file}")
            
            return data
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(response.text)
            return None
    
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out after {elapsed:.1f}s")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def test_timeline(concept: str):
    """Test timeline endpoint."""
    print_header(f"4. GET TIMELINE: '{concept.upper()}'")
    
    try:
        response = requests.get(
            f"{BASE_URL}/timeline",
            params={"concept": concept, "top_n": 3}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Concept: {data['concept']}")
            print(f"\n📈 Timeline Evolution:")
            
            for entry in data['timeline']:
                print(f"\n  {entry['era']}:")
                print(f"    Semantic shift: {entry['centroid_shift_from_prev']:.4f}")
                print(f"    Top matches:")
                for item in entry['top']:
                    # Truncate long text
                    text = item['text']
                    if len(text) > 70:
                        text = text[:67] + "..."
                    print(f"      • {text}")
                    print(f"        (similarity: {item['score']:.3f})")
            
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            if response.status_code == 404:
                print("→ Generate embeddings first using /build-embeddings")
            print(response.text)
            return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def run_full_demo():
    """Run complete demo."""
    print("\n" + "="*70)
    print("  ECHOES BACKEND - OPENROUTER DEMO")
    print("="*70)
    
    # Configuration
    word = "privacy"
    eras = ["1900s", "1960s", "2020s"]
    
    print(f"\nDemo word: '{word}'")
    print(f"Demo eras: {', '.join(eras)}")
    
    # 1. Health check
    if not check_health():
        print("\n❌ Server is not healthy. Exiting.")
        return
    
    # 2. Generate evolution
    input("\n⏎ Press Enter to generate evolution data...")
    evolution = test_generate_evolution(word, eras)
    if not evolution:
        print("\n⚠️  Evolution generation failed. Check your API key and internet connection.")
        return
    
    # 3. Build embeddings
    input("\n⏎ Press Enter to build embeddings...")
    embeddings = test_build_embeddings(word, eras)
    if not embeddings:
        print("\n⚠️  Embedding creation failed.")
        return
    
    # 4. Get timeline
    input("\n⏎ Press Enter to view timeline...")
    timeline = test_timeline(word)
    
    # Summary
    print_header("DEMO COMPLETE ✅")
    print(f"""
Summary:
  • Generated {evolution.get('total_examples', 0)} contextual examples
  • Created {embeddings.get('total_items', 0)} embeddings
  • Analyzed semantic evolution across {len(eras)} time periods
  • Used model: {evolution.get('model', 'unknown')}

Next steps:
  1. Check the 'embeddings/{word}/' folder for generated files
  2. Try different words and time periods
  3. Explore the API docs at http://localhost:8000/docs
  4. Build a frontend to visualize the data!
    """)


if __name__ == "__main__":
    try:
        run_full_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")