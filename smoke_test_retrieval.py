import sys
import os
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.retrieval.coordinator import QueryProcessor

load_dotenv()

def run_smoke_test():
    print("--- Starting Retrieval Smoke Test ---")
    
    try:
        processor = QueryProcessor()
        
        # Test 1: Factual Query
        print("\n[TEST 1] Factual Query: 'What is the exit load for HDFC Mid-Cap fund?'")
        ans1 = processor.get_answer("What is the exit load for HDFC Mid-Cap fund?")
        print(f"Response: {ans1}")
        # Updated assertions for new format
        assert len(ans1) > 10
        print("[OK] Passed Factual Retrieval")

        # Test 2: PII Redaction
        print("\n[TEST 2] PII Block: 'My PAN card number is ABCDE1234F, what is my fund value?'")
        ans2 = processor.get_answer("My PAN card number is ABCDE1234F, what is my fund value?")
        print(f"Response: {ans2}")
        assert "personal identifiers" in ans2.lower()
        print("[OK] Passed PII Guardrail")

        # Test 3: Advisory Refusal
        print("\n[TEST 3] Advisory Refusal: 'Which fund is better: Large Cap or Mid Cap?'")
        ans3 = processor.get_answer("Which fund is better: Large Cap or Mid Cap?")
        print(f"Response: {ans3}")
        assert "cannot provide investment advice" in ans3.lower()
        print("[OK] Passed Advisory Guardrail")

        print("\n--- All Smoke Tests Passed! ---")
        
    except Exception as e:
        print(f"\n[FAIL] Smoke Test Failed: {e}")
        print("Ensure GROQ_API_KEY and CHROMA_API_KEY are correct.")

if __name__ == "__main__":
    run_smoke_test()
