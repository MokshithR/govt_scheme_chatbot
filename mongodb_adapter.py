import os
import pymongo
from datetime import datetime
from typing import List, Dict, Optional

class MongoDBAdapter:
    """MongoDB adapter for government schemes"""
    
    def __init__(self):
        self.client = pymongo.MongoClient('mongodb://localhost:27017/')
        self.db = self.client['Govt_schemes']  # Match case with existing database
        self.schemes_collection = self.db['government_schemes']
    
    def search_schemes(self, query: str, keywords: List[str], entities: Dict, intent: str) -> List[Dict]:
        """Search schemes in MongoDB"""
        try:
            # Start with active schemes
            filter_query = {"is_active": True}
            
            # Apply sector filter
            if entities.get('sectors'):
                filter_query["sector"] = {"$in": entities['sectors']}
            
            # Break query into words for more flexible matching
            query_words = query.lower().split()
            
            # Apply keyword search with more flexible matching
            if keywords:
                keyword_regex = "|".join(keywords)
                filter_query["$or"] = [
                    {"title": {"$regex": keyword_regex, "$options": "i"}},
                    {"description": {"$regex": keyword_regex, "$options": "i"}},
                    {"keywords": {"$elemMatch": {"$regex": keyword_regex, "$options": "i"}}},
                    {"search_tags": {"$elemMatch": {"$regex": keyword_regex, "$options": "i"}}}
                ]
            else:
                # If no keywords, use more flexible query matching
                # Create regex patterns for each word in the query
                word_patterns = [f".*{word}.*" for word in query_words]
                combined_pattern = "|".join(word_patterns)
                
                filter_query["$or"] = [
                    {"title": {"$regex": combined_pattern, "$options": "i"}},
                    {"description": {"$regex": combined_pattern, "$options": "i"}},
                    {"keywords": {"$elemMatch": {"$regex": combined_pattern, "$options": "i"}}},
                    {"search_tags": {"$elemMatch": {"$regex": combined_pattern, "$options": "i"}}}
                ]
            
            # Additional filtering based on intent
            if intent == 'eligibility':
                filter_query["eligibility_criteria"] = {"$exists": True, "$ne": ""}
            elif intent == 'application':
                filter_query["application_process"] = {"$exists": True, "$ne": ""}
            elif intent == 'benefits':
                filter_query["benefits"] = {"$exists": True, "$ne": ""}
            
            # Execute query without text score
            schemes = list(self.schemes_collection.find(
                filter_query
            ).limit(10))
            
            # Convert ObjectId to string for JSON serialization
            for scheme in schemes:
                scheme['_id'] = str(scheme['_id'])
            
            return schemes
            
        except Exception as e:
            print(f"MongoDB search error: {e}")
            return []
    
    def advanced_search(self, query: str, keywords: List[str], entities: Dict, 
                       sector: str = '', ministry: str = '', eligibility: str = '', 
                       sort_by: str = 'relevance') -> List[Dict]:
        """
        Advanced search with enhanced filtering and sorting
        """
        try:
            # Start with active schemes
            filter_query = {"is_active": True}
            
            # Sector filter
            if sector:
                filter_query["sector"] = {"$regex": sector, "$options": "i"}
            
            # Ministry filter
            if ministry:
                filter_query["ministry"] = {"$regex": ministry, "$options": "i"}
            
            # Eligibility filter
            if eligibility:
                eligibility_words = eligibility.lower().split()
                eligibility_patterns = [f".*{word}.*" for word in eligibility_words]
                eligibility_regex = "|".join(eligibility_patterns)
                filter_query["eligibility_criteria"] = {"$regex": eligibility_regex, "$options": "i"}
            
            # Keyword search (if provided)
            if keywords:
                keyword_regex = "|".join([f".*{kw}.*" for kw in keywords])
                filter_query["$or"] = [
                    {"title": {"$regex": keyword_regex, "$options": "i"}},
                    {"description": {"$regex": keyword_regex, "$options": "i"}},
                    {"short_description": {"$regex": keyword_regex, "$options": "i"}},
                    {"keywords": {"$elemMatch": {"$regex": keyword_regex, "$options": "i"}}},
                    {"search_tags": {"$elemMatch": {"$regex": keyword_regex, "$options": "i"}}},
                    {"benefits": {"$regex": keyword_regex, "$options": "i"}}
                ]
            
            # Execute query with sorting
            cursor = self.schemes_collection.find(filter_query)
            
            # Apply sorting
            if sort_by == 'alphabetical':
                cursor = cursor.sort("title", 1)  # Ascending
            elif sort_by == 'newest':
                cursor = cursor.sort("created_date", -1)  # Descending
            elif sort_by == 'oldest':
                cursor = cursor.sort("created_date", 1)  # Ascending
            # For 'relevance', keep original order (no sorting)
            
            # Limit results to prevent overwhelming response
            schemes = list(cursor.limit(50))
            
            # Convert ObjectId to string for JSON serialization
            for scheme in schemes:
                scheme['_id'] = str(scheme['_id'])
            
            return schemes
            
        except Exception as e:
            print(f"MongoDB advanced search error: {e}")
            return []
    
    def get_scheme_by_id(self, scheme_id: str) -> Optional[Dict]:
        """Get a specific scheme by ID"""
        try:
            from bson import ObjectId
            scheme = self.schemes_collection.find_one({"_id": ObjectId(scheme_id)})
            if scheme:
                scheme['_id'] = str(scheme['_id'])
            return scheme
        except Exception as e:
            print(f"MongoDB get scheme error: {e}")
            return None
    
    def get_schemes_by_sector(self, sector: str) -> List[Dict]:
        """Get all schemes for a specific sector"""
        try:
            schemes = list(self.schemes_collection.find({
                "sector": sector,
                "is_active": True
            }))
            
            for scheme in schemes:
                scheme['_id'] = str(scheme['_id'])
            
            return schemes
        except Exception as e:
            print(f"MongoDB sector search error: {e}")
            return []
    
    def get_all_active_schemes(self) -> List[Dict]:
        """Get all active schemes"""
        try:
            schemes = list(self.schemes_collection.find({"is_active": True}))
            
            for scheme in schemes:
                scheme['_id'] = str(scheme['_id'])
            
            return schemes
        except Exception as e:
            print(f"MongoDB get all schemes error: {e}")
            return []
    
    def get_total_schemes(self) -> int:
        """Get total number of schemes in database"""
        try:
            return self.schemes_collection.count_documents({})
        except Exception as e:
            print(f"Error getting total schemes: {e}")
            return 0
    
    def get_scheme_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            total_schemes = self.schemes_collection.count_documents({})
            active_schemes = self.schemes_collection.count_documents({"is_active": True})
            
            sectors = self.schemes_collection.distinct("sector")
            sector_counts = {}
            for sector in sectors:
                count = self.schemes_collection.count_documents({"sector": sector, "is_active": True})
                sector_counts[sector] = count
            
            return {
                "total_schemes": total_schemes,
                "active_schemes": active_schemes,
                "sectors": sector_counts
            }
        except Exception as e:
            print(f"MongoDB statistics error: {e}")
            return {"total_schemes": 0, "active_schemes": 0, "sectors": {}}

# Test the adapter
if __name__ == "__main__":
    adapter = MongoDBAdapter()
    
    print("Testing MongoDB Adapter:")
    print("=" * 40)
    
    # Test statistics
    stats = adapter.get_scheme_statistics()
    print(f"Total schemes: {stats['total_schemes']}")
    print(f"Active schemes: {stats['active_schemes']}")
    print("Sectors:")
    for sector, count in stats['sectors'].items():
        print(f"  - {sector}: {count} schemes")
    
    # Test search
    print("\nTesting search:")
    schemes = adapter.search_schemes(
        "What are the agriculture schemes available?",
        ["agriculture", "schemes"],
        {"sectors": ["agriculture"]},
        "sector_specific"
    )
    print(f"Found {len(schemes)} agriculture schemes")
    for scheme in schemes[:3]:
        print(f"  - {scheme['title']}")
