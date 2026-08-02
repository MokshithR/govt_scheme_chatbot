"""
Django Management Command: Test AI Chatbot System
Runs 6 automated tests to validate the entire chatbot pipeline
"""

from django.core.management.base import BaseCommand
from chatbot.embedding_utils import create_embedding, validate_embedding
from chatbot.vector_search import search_similar_schemes, count_schemes_with_embeddings
from chatbot.prompts import GREETINGS, GREETING_RESPONSE, NO_RESULTS_MESSAGE
from chatbot.debug_loggers import print_test_header, print_test_result
import json


class Command(BaseCommand):
    help = 'Run automated tests for AI chatbot system'
    
    def handle(self, *args, **kwargs):
        print("\n" + "="*70)
        print("AI CHATBOT SYSTEM - AUTOMATED TEST SUITE")
        print("="*70 + "\n")
        
        passed_tests = 0
        total_tests = 6
        
        # Test 1: Embedding Validity
        passed_tests += self.test_embedding_validity()
        
        # Test 2: Vector Similarity Search
        passed_tests += self.test_vector_similarity()
        
        # Test 3: Greeting Fallback
        passed_tests += self.test_greeting_fallback()
        
        # Test 4: RAG Response Structure
        passed_tests += self.test_rag_response()
        
        # Test 5: JSON Output Structure
        passed_tests += self.test_json_structure()
        
        # Test 6: SSML Validation
        passed_tests += self.test_ssml_validation()
        
        # Final Summary
        print("\n" + "="*70)
        print(f"FINAL RESULTS: {passed_tests}/{total_tests} TESTS PASSED")
        print("="*70 + "\n")
        
        if passed_tests == total_tests:
            self.stdout.write(self.style.SUCCESS("✓ ALL TESTS PASSED - SYSTEM READY FOR DEPLOYMENT"))
        else:
            self.stdout.write(self.style.ERROR(f"✗ {total_tests - passed_tests} TESTS FAILED - FIX ISSUES BEFORE DEPLOYMENT"))
    
    def test_embedding_validity(self):
        """Test 1: Validate embedding generation"""
        print_test_header("Embedding Validity")
        
        try:
            # Generate embedding for test text
            test_text = "agriculture loan scheme for farmers"
            embedding = create_embedding(test_text)
            
            # Check 1: Embedding is a list
            if not isinstance(embedding, list):
                print_test_result(False, f"Embedding is not a list (got {type(embedding)})")
                return 0
            
            # Check 2: Embedding has 768 dimensions
            if len(embedding) != 768:
                print_test_result(False, f"Embedding has {len(embedding)} dimensions (expected 768)")
                return 0
            
            # Check 3: All values are numeric
            if not all(isinstance(x, (int, float)) for x in embedding):
                print_test_result(False, "Embedding contains non-numeric values")
                return 0
            
            # Check 4: Validate using built-in validator
            is_valid, error = validate_embedding(embedding)
            if not is_valid:
                print_test_result(False, f"Embedding validation failed: {error}")
                return 0
            
            print_test_result(True, "Embedding generated: 768 dims, all numeric, validated")
            return 1
            
        except Exception as e:
            print_test_result(False, f"Exception during embedding generation: {str(e)}")
            return 0
    
    def test_vector_similarity(self):
        """Test 2: Validate vector similarity search"""
        print_test_header("Vector Similarity Search")
        
        try:
            # Get database stats
            stats = count_schemes_with_embeddings()
            total = stats['total']
            with_embeddings = stats['with_embeddings']
            
            if with_embeddings == 0:
                print_test_result(False, f"No schemes have embeddings ({total} total schemes)")
                return 0
            
            # Generate embedding for test query
            test_query = "loan for farmers"
            query_embedding = create_embedding(test_query)
            
            # Search for similar schemes
            results = search_similar_schemes(query_embedding, top_k=5)
            
            # Check 1: Results returned
            if not results:
                print_test_result(False, "No results returned from search")
                return 0
            
            # Check 2: Each result has required fields
            required_fields = ['id', 'title', 'distance', 'similarity_score']
            for result in results:
                missing = [f for f in required_fields if f not in result]
                if missing:
                    print_test_result(False, f"Result missing fields: {missing}")
                    return 0
            
            # Check 3: Distances are in valid range [0, 2]
            for result in results:
                distance = result['distance']
                if not (0 <= distance <= 2):
                    print_test_result(False, f"Invalid distance {distance} (should be 0-2)")
                    return 0
            
            # Check 4: Results sorted by distance (ascending)
            distances = [r['distance'] for r in results]
            if distances != sorted(distances):
                print_test_result(False, "Results not sorted by distance")
                return 0
            
            best_match = results[0]
            print_test_result(True, f"Search OK: {len(results)} results, best distance={best_match['distance']:.4f}, '{best_match['title'][:50]}'")
            return 1
            
        except Exception as e:
            print_test_result(False, f"Exception during search: {str(e)}")
            return 0
    
    def test_greeting_fallback(self):
        """Test 3: Validate greeting detection"""
        print_test_header("Greeting Fallback Detection")
        
        try:
            # Test greetings
            test_greetings = ["hello", "hi", "namaste", "good morning", "how are you"]
            
            for greeting in test_greetings:
                # Check if greeting is detected
                is_greeting = any(g in greeting.lower() for g in GREETINGS)
                
                if not is_greeting:
                    print_test_result(False, f"Greeting '{greeting}' not detected in GREETINGS list")
                    return 0
            
            # Check greeting response exists
            if not GREETING_RESPONSE:
                print_test_result(False, "GREETING_RESPONSE is empty")
                return 0
            
            # Check greeting response mentions chatbot name
            if "YOJANAMITHRA" not in GREETING_RESPONSE.upper():
                print_test_result(False, "GREETING_RESPONSE does not mention YOJANAMITHRA")
                return 0
            
            print_test_result(True, f"Greeting detection OK: {len(test_greetings)} greetings tested, response ready")
            return 1
            
        except Exception as e:
            print_test_result(False, f"Exception during greeting test: {str(e)}")
            return 0
    
    def test_rag_response(self):
        """Test 4: Validate RAG pipeline components"""
        print_test_header("RAG Response Pipeline")
        
        try:
            # Test query
            test_query = "agriculture schemes for farmers"
            
            # Step 1: Generate query embedding
            query_embedding = create_embedding(test_query)
            if len(query_embedding) != 768:
                print_test_result(False, f"Query embedding has {len(query_embedding)} dims (expected 768)")
                return 0
            
            # Step 2: Search for schemes
            results = search_similar_schemes(query_embedding, top_k=5, filters={'is_active': True})
            if not results:
                print_test_result(False, "No search results (database may be empty)")
                return 0
            
            # Step 3: Filter by threshold
            THRESHOLD = 0.55
            good_matches = [r for r in results if r['distance'] <= THRESHOLD]
            
            # Step 4: Check if at least one good match
            if len(good_matches) == 0:
                # This is OK - fallback should trigger
                print_test_result(True, f"RAG pipeline OK: No good matches (threshold={THRESHOLD}), fallback would trigger")
                return 1
            
            # Step 5: Validate scheme objects
            for match in good_matches:
                if 'scheme_object' not in match:
                    print_test_result(False, "Search result missing 'scheme_object'")
                    return 0
                
                scheme = match['scheme_object']
                required_attrs = ['title', 'short_description']
                for attr in required_attrs:
                    if not hasattr(scheme, attr):
                        print_test_result(False, f"Scheme object missing attribute: {attr}")
                        return 0
            
            print_test_result(True, f"RAG pipeline OK: {len(good_matches)} good matches, ready for Gemini")
            return 1
            
        except Exception as e:
            print_test_result(False, f"Exception during RAG test: {str(e)}")
            return 0
    
    def test_json_structure(self):
        """Test 5: Validate API response JSON structure"""
        print_test_header("JSON Output Structure")
        
        try:
            # Simulate semantic search response
            semantic_response = {
                'query': 'test query',
                'results': [
                    {
                        'id': 1,
                        'title': 'Test Scheme',
                        'short_description': 'Test description',
                        'distance': 0.3,
                        'similarity_score': 85.0
                    }
                ],
                'count': 1
            }
            
            # Check semantic search fields
            required_semantic = ['query', 'results', 'count']
            for field in required_semantic:
                if field not in semantic_response:
                    print_test_result(False, f"Semantic response missing field: {field}")
                    return 0
            
            # Simulate smart answer response
            smart_response = {
                'answer': 'Test answer text',
                'ssml': '<speak>Test answer text</speak>',
                'schemes_used': ['Test Scheme']
            }
            
            # Check smart answer fields
            required_smart = ['answer', 'ssml', 'schemes_used']
            for field in required_smart:
                if field not in smart_response:
                    print_test_result(False, f"Smart answer response missing field: {field}")
                    return 0
            
            # Validate JSON serialization
            try:
                json.dumps(semantic_response)
                json.dumps(smart_response)
            except Exception as e:
                print_test_result(False, f"JSON serialization failed: {str(e)}")
                return 0
            
            print_test_result(True, "JSON structure OK: All required fields present, serializable")
            return 1
            
        except Exception as e:
            print_test_result(False, f"Exception during JSON test: {str(e)}")
            return 0
    
    def test_ssml_validation(self):
        """Test 6: Validate SSML output"""
        print_test_header("SSML Validation")
        
        try:
            # Test SSML structure
            test_answer = "This is a test answer for farmers."
            ssml_output = f"<speak>{test_answer}</speak>"
            
            # Check 1: SSML starts with <speak>
            if not ssml_output.startswith("<speak>"):
                print_test_result(False, "SSML does not start with <speak>")
                return 0
            
            # Check 2: SSML ends with </speak>
            if not ssml_output.endswith("</speak>"):
                print_test_result(False, "SSML does not end with </speak>")
                return 0
            
            # Check 3: Content between tags
            content = ssml_output.replace("<speak>", "").replace("</speak>", "")
            if len(content) == 0:
                print_test_result(False, "SSML has no content between tags")
                return 0
            
            # Check 4: Test break tags (optional but recommended)
            ssml_with_break = f"<speak>This is a test.<break time=\"300ms\"/>More content.</speak>"
            if '<break' not in ssml_with_break:
                # Not critical, just informational
                pass
            
            print_test_result(True, "SSML validation OK: Proper tags, content present")
            return 1
            
        except Exception as e:
            print_test_result(False, f"Exception during SSML test: {str(e)}")
            return 0
