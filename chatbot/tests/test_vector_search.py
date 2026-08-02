"""
Unit tests for pgvector + Gemini semantic search system.

Run with: python manage.py test chatbot.tests.test_vector_search
"""

import os
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from chatbot.models import GovernmentScheme, Sector, UserProfile
from chatbot.vector_search import VectorSearchService, get_vector_search_service
from chatbot.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


class VectorSearchServiceTests(TransactionTestCase):
    """Test VectorSearchService class."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set mock API key for tests
        os.environ['GEMINI_API_KEY'] = 'test-api-key-12345'
    
    def setUp(self):
        """Set up test data."""
        # Create test sector
        self.sector = Sector.objects.create(
            name='Agriculture',
            description='Agricultural schemes'
        )
        
        # Create test scheme
        self.scheme = GovernmentScheme.objects.create(
            title='PM-KISAN: Direct Income Support for Farmers',
            description='Financial assistance to farmers',
            short_description='₹6000 per year to farmers',
            sector=self.sector,
            ministry='Ministry of Agriculture',
            department='Department of Agriculture',
            government_level='central',
            eligibility_criteria='Small and marginal farmers',
            benefits='₹6000 per year in 3 installments',
            application_process='Register on PM-KISAN portal',
            launch_date='2019-02-01',
            source_url='https://pmkisan.gov.in',
        )
    
    @patch('chatbot.vector_search.genai.embed_content')
    def test_generate_query_embedding(self, mock_embed):
        """Test query embedding generation."""
        # Mock Gemini API response
        mock_embed.return_value = {
            'embedding': [0.1] * 768  # 768-dimensional vector
        }
        
        service = VectorSearchService()
        embedding = service.generate_query_embedding('schemes for farmers')
        
        self.assertEqual(len(embedding), 768)
        mock_embed.assert_called_once()
        self.assertEqual(mock_embed.call_args[1]['task_type'], 'retrieval_query')
    
    @patch('chatbot.vector_search.genai.embed_content')
    def test_generate_query_embedding_invalid_dimension(self, mock_embed):
        """Test that invalid embedding dimensions raise error."""
        # Mock invalid dimension response
        mock_embed.return_value = {
            'embedding': [0.1] * 512  # Wrong dimension
        }
        
        service = VectorSearchService()
        
        with self.assertRaises(ValueError) as context:
            service.generate_query_embedding('test query')
        
        self.assertIn('Invalid embedding dimension', str(context.exception))
    
    @patch('chatbot.vector_search.genai.GenerativeModel')
    def test_generate_llm_response(self, mock_model_class):
        """Test LLM response generation."""
        # Mock Gemini LLM response
        mock_response = MagicMock()
        mock_response.text = "PM-KISAN provides ₹6000/year to farmers. Eligibility: Small farmers. Apply: pmkisan.gov.in"
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        service = VectorSearchService()
        
        schemes = [{
            'id': 1,
            'title': 'PM-KISAN',
            'sector': 'Agriculture',
            'government_level': 'central',
            'eligibility_criteria': 'Small farmers',
            'benefits': '₹6000 per year',
            'application_process': 'Register online',
            'website': 'https://pmkisan.gov.in',
            'similarity_score': 0.85,
        }]
        
        answer = service.generate_llm_response(
            user_query='What schemes are available for farmers?',
            retrieved_schemes=schemes,
        )
        
        self.assertIn('PM-KISAN', answer)
        mock_model.generate_content.assert_called_once()
    
    @patch('chatbot.vector_search.genai.GenerativeModel')
    def test_generate_llm_response_no_schemes(self, mock_model_class):
        """Test LLM response when no schemes found."""
        service = VectorSearchService()
        
        answer = service.generate_llm_response(
            user_query='schemes for aliens',
            retrieved_schemes=[],
        )
        
        self.assertIn('No official scheme found', answer)
        # Should not call LLM if no schemes
        mock_model_class.assert_not_called()
    
    def test_singleton_pattern(self):
        """Test that get_vector_search_service returns singleton."""
        service1 = get_vector_search_service()
        service2 = get_vector_search_service()
        
        self.assertIs(service1, service2)


class VectorSearchAPITests(TestCase):
    """Test vector search API endpoint."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ['GEMINI_API_KEY'] = 'test-api-key-12345'
    
    def setUp(self):
        """Set up test user and scheme."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.sector = Sector.objects.create(name='Health')
        
        self.scheme = GovernmentScheme.objects.create(
            title='Ayushman Bharat',
            description='Health insurance scheme',
            sector=self.sector,
            ministry='Ministry of Health',
            department='Health Department',
            government_level='central',
            eligibility_criteria='Poor families',
            benefits='₹5 lakh health cover',
            application_process='Apply at health center',
            launch_date='2018-09-23',
            source_url='https://pmjay.gov.in',
        )
    
    @patch('chatbot.views.get_vector_search_service')
    def test_vector_search_api_success(self, mock_service_getter):
        """Test successful vector search API call."""
        # Mock service
        mock_service = MagicMock()
        mock_service.search.return_value = {
            'answer': 'Ayushman Bharat provides health insurance.',
            'schemes': [{
                'id': 1,
                'title': 'Ayushman Bharat',
                'similarity_score': 0.9,
            }],
            'query': 'health schemes',
            'top_k': 5,
        }
        mock_service_getter.return_value = mock_service
        
        response = self.client.post(
            '/api/vector-search/',
            data={'query': 'health schemes'},
            content_type='application/json',
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('Ayushman Bharat', data['answer'])
        self.assertEqual(len(data['schemes']), 1)
        self.assertIn('ssml', data)  # Check SSML is included
    
    @patch('chatbot.views.get_vector_search_service')
    def test_search_api_endpoint(self, mock_service_getter):
        """Test new /api/search/ endpoint."""
        mock_service = MagicMock()
        mock_service.search.return_value = {
            'answer': 'Ayushman Bharat provides health insurance.',
            'schemes': [{
                'id': 1,
                'title': 'Ayushman Bharat',
                'similarity_score': 0.9,
            }],
            'query': 'health schemes',
            'top_k': 5,
        }
        mock_service_getter.return_value = mock_service
        
        response = self.client.post(
            '/api/search/',
            data={'query': 'health schemes'},
            content_type='application/json',
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('answer', data)
        self.assertIn('schemes', data)
        self.assertIn('ssml', data)
    
    def test_vector_search_api_missing_query(self):
        """Test API with missing query parameter."""
        response = self.client.post(
            '/api/vector-search/',
            data={},
            content_type='application/json',
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Query parameter is required', data['error'])
    
    @patch('chatbot.views.get_vector_search_service')
    def test_vector_search_api_with_filters(self, mock_service_getter):
        """Test API with sector and government level filters."""
        mock_service = MagicMock()
        mock_service.search.return_value = {
            'answer': 'Health schemes found.',
            'schemes': [],
            'query': 'test',
            'top_k': 3,
        }
        mock_service_getter.return_value = mock_service
        
        response = self.client.post(
            '/api/vector-search/',
            data={
                'query': 'health insurance',
                'top_k': 3,
                'sector': 'Health',
                'government_level': 'central',
                'use_llm': True,
                'llm_model': 'gemini-1.5-pro',
            },
            content_type='application/json',
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify service was called with correct parameters
        mock_service.search.assert_called_once_with(
            query='health insurance',
            top_k=3,
            sector_filter='Health',
            government_level_filter='central',
            use_llm_reranking=True,
            llm_model='gemini-1.5-pro',
        )


class PromptTests(TestCase):
    """Test prompt templates."""
    
    def test_system_prompt_contains_rules(self):
        """Test that system prompt has critical rules."""
        self.assertIn('NEVER make up', SYSTEM_PROMPT)
        self.assertIn('No official scheme found', SYSTEM_PROMPT)
        self.assertIn('YOJANAMITHRA', SYSTEM_PROMPT)
        self.assertIn('government scheme', SYSTEM_PROMPT.lower())
    
    def test_user_prompt_template_formatting(self):
        """Test user prompt template can be formatted."""
        context = "Scheme: PM-KISAN\nBenefits: ₹6000/year"
        query = "What are farmer schemes?"
        
        formatted = USER_PROMPT_TEMPLATE.format(
            context=context,
            user_query=query,
        )
        
        self.assertIn(context, formatted)
        self.assertIn(query, formatted)
        self.assertIn('CONTEXT', formatted)
        self.assertIn('USER QUESTION', formatted)
