"""
Enhanced LightRAG Knowledge Graph integration with improved AGE support.

This enhanced version adds better error handling, graph construction from crawled data,
and advanced graph analytics.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from .database import get_db_connection
from .utils import create_embedding

logger = logging.getLogger(__name__)


class KnowledgeGraphManager:
    """Enhanced knowledge graph manager with advanced AGE integration."""
    
    def __init__(self, graph_name: str = "lightrag_graph"):
        self.graph_name = graph_name
        self._age_available = None
    
    async def check_age_availability(self) -> bool:
        """Check if Apache AGE is available and properly configured."""
        if self._age_available is not None:
            return self._age_available
        
        db = await get_db_connection()
        try:
            # Check if AGE extension exists
            result = await db.fetchval(
                "SELECT COUNT(*) FROM pg_extension WHERE extname = 'age'"
            )
            if result == 0:
                logger.warning("Apache AGE extension not found")
                self._age_available = False
                return False
            
            # Check if graph exists
            await db.execute("SET search_path = ag_catalog, '$user', public;")
            
            # Try to access the graph
            await db.fetchval(f"SELECT ag_catalog.graph_exists('{self.graph_name}')")
            self._age_available = True
            return True
            
        except Exception as e:
            logger.error(f"AGE availability check failed: {e}")
            self._age_available = False
            return False
    
    async def ensure_graph_exists(self) -> bool:
        """Ensure the knowledge graph exists, create if necessary."""
        if not await self.check_age_availability():
            return False
        
        db = await get_db_connection()
        try:
            await db.execute("SET search_path = ag_catalog, '$user', public;")
            
            # Check if graph exists
            exists = await db.fetchval(
                f"SELECT ag_catalog.graph_exists('{self.graph_name}')"
            )
            
            if not exists:
                # Create the graph
                await db.fetchval(
                    f"SELECT ag_catalog.create_graph('{self.graph_name}')"
                )
                logger.info(f"Created knowledge graph: {self.graph_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure graph exists: {e}")
            return False
    
    async def execute_cypher(self, cypher_query: str, parameters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query with enhanced error handling."""
        if not await self.ensure_graph_exists():
            logger.warning("AGE not available, returning empty results")
            return []
        
        db = await get_db_connection()
        try:
            await db.execute("SET search_path = ag_catalog, '$user', public;")
            
            # Format parameters if provided
            if parameters:
                # Simple parameter substitution - in production, use proper parameter binding
                for key, value in parameters.items():
                    if isinstance(value, str):
                        cypher_query = cypher_query.replace(f"${key}", f"'{value}'")
                    else:
                        cypher_query = cypher_query.replace(f"${key}", str(value))
            
            # Execute the Cypher query
            sql_query = f"""
            SELECT * FROM ag_catalog.cypher('{self.graph_name}', $$
            {cypher_query}
            $$) as (result agtype);
            """
            
            results = await db.fetch(sql_query)
            
            # Convert AGE results to Python objects
            processed_results = []
            for row in results:
                result = row['result']
                if result is not None:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Cypher query execution failed: {e}")
            logger.error(f"Query: {cypher_query}")
            return []
    
    async def build_graph_from_documents(self, limit: int = 100) -> Dict[str, Any]:
        """Build knowledge graph from crawled documents using NLP extraction."""
        if not await self.ensure_graph_exists():
            return {"success": False, "error": "AGE not available"}
        
        try:
            db = await get_db_connection()
            
            # Get recent documents to process
            documents = await db.fetch(
                """
                SELECT id, url, content, metadata
                FROM crawl.crawled_pages
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit
            )
            
            entities_created = 0
            relationships_created = 0
            
            for doc in documents:
                # Extract entities and relationships from document content
                # This is a simplified example - in production, use proper NLP
                entities = await self._extract_entities_from_text(doc['content'])
                relationships = await self._extract_relationships_from_text(doc['content'])
                
                # Create entities in the graph
                for entity in entities:
                    await self._create_entity_if_not_exists(entity, doc['url'])
                    entities_created += 1
                
                # Create relationships
                for rel in relationships:
                    await self._create_relationship_if_not_exists(rel, doc['url'])
                    relationships_created += 1
            
            return {
                "success": True,
                "documents_processed": len(documents),
                "entities_created": entities_created,
                "relationships_created": relationships_created
            }
            
        except Exception as e:
            logger.error(f"Failed to build graph from documents: {e}")
            return {"success": False, "error": str(e)}
    
    async def _extract_entities_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text using simple patterns (enhance with proper NLP)."""
        import re
        
        entities = []
        
        # Simple patterns for demonstration - use proper NLP in production
        # Extract potential person names (capitalized words)
        person_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        persons = re.findall(person_pattern, text)
        
        for person in set(persons):
            entities.append({
                "name": person,
                "type": "Person",
                "description": f"Person mentioned in text",
                "properties": {"source": "text_extraction"}
            })
        
        # Extract organizations (words ending with Corp, Inc, Ltd, etc.)
        org_pattern = r'\b[A-Z][a-z\s]+(Corp|Inc|Ltd|LLC|Company|Organization)\b'
        orgs = re.findall(org_pattern, text)
        
        for org in set(orgs):
            entities.append({
                "name": org,
                "type": "Organization", 
                "description": f"Organization mentioned in text",
                "properties": {"source": "text_extraction"}
            })
        
        return entities[:10]  # Limit to prevent overwhelming the graph
    
    async def _extract_relationships_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract relationships from text using simple patterns."""
        # Simplified relationship extraction - enhance with proper NLP
        relationships = []
        
        # Look for "works at" patterns
        import re
        work_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+) works at ([A-Z][a-z\s]+(?:Corp|Inc|Ltd|LLC|Company))'
        work_matches = re.findall(work_pattern, text)
        
        for person, org in work_matches:
            relationships.append({
                "start_entity": person,
                "end_entity": org,
                "type": "WORKS_AT",
                "properties": {"confidence": 0.8, "source": "text_extraction"}
            })
        
        return relationships[:5]  # Limit relationships
    
    async def _create_entity_if_not_exists(self, entity: Dict[str, Any], source_url: str):
        """Create an entity in the graph if it doesn't exist."""
        cypher_query = f"""
        MERGE (e:{entity['type']} {{name: '{entity['name']}'}})
        ON CREATE SET 
            e.description = '{entity.get('description', '')}',
            e.properties = {json.dumps(entity.get('properties', {}))},
            e.source_url = '{source_url}',
            e.created_at = timestamp()
        RETURN e
        """
        
        await self.execute_cypher(cypher_query)
    
    async def _create_relationship_if_not_exists(self, rel: Dict[str, Any], source_url: str):
        """Create a relationship in the graph if it doesn't exist."""
        cypher_query = f"""
        MATCH (a {{name: '{rel['start_entity']}'}}), (b {{name: '{rel['end_entity']}'}})
        MERGE (a)-[r:{rel['type']}]->(b)
        ON CREATE SET 
            r.properties = {json.dumps(rel.get('properties', {}))},
            r.source_url = '{source_url}',
            r.created_at = timestamp()
        RETURN r
        """
        
        await self.execute_cypher(cypher_query)
    
    async def analyze_graph_patterns(self) -> Dict[str, Any]:
        """Analyze common patterns and structures in the knowledge graph."""
        if not await self.check_age_availability():
            return {"error": "AGE not available"}
        
        analysis = {}
        
        try:
            # Find central entities (high degree)
            central_entities = await self.execute_cypher("""
                MATCH (n)
                WITH n, size((n)--()) as degree
                WHERE degree > 3
                RETURN n.name as name, labels(n)[0] as type, degree
                ORDER BY degree DESC
                LIMIT 10
            """)
            analysis["central_entities"] = central_entities
            
            # Find isolated entities
            isolated_entities = await self.execute_cypher("""
                MATCH (n)
                WHERE NOT (n)--()
                RETURN n.name as name, labels(n)[0] as type
                LIMIT 10
            """)
            analysis["isolated_entities"] = isolated_entities
            
            # Find triangular relationships (potential communities)
            triangles = await self.execute_cypher("""
                MATCH (a)-[:RELATED_TO]-(b)-[:RELATED_TO]-(c)-[:RELATED_TO]-(a)
                WHERE id(a) < id(b) AND id(b) < id(c)
                RETURN a.name, b.name, c.name
                LIMIT 10
            """)
            analysis["triangular_patterns"] = triangles
            
            # Find shortest paths between different entity types
            cross_type_paths = await self.execute_cypher("""
                MATCH path = shortestPath((p:Person)-[*..3]-(o:Organization))
                RETURN p.name as person, o.name as organization, length(path) as distance
                ORDER BY distance
                LIMIT 10
            """)
            analysis["cross_type_connections"] = cross_type_paths
            
            return analysis
            
        except Exception as e:
            logger.error(f"Graph pattern analysis failed: {e}")
            return {"error": str(e)}
    
    async def suggest_new_relationships(self, entity_name: str) -> List[Dict[str, Any]]:
        """Suggest potential new relationships for an entity based on graph structure."""
        if not await self.check_age_availability():
            return []
        
        try:
            # Find entities 2 hops away (potential indirect connections)
            suggestions = await self.execute_cypher(f"""
                MATCH (target {{name: '{entity_name}'}})
                MATCH (target)-[]->(intermediate)-[]->(suggested)
                WHERE suggested <> target AND NOT (target)-[]->(suggested)
                WITH suggested, count(*) as connection_strength
                WHERE connection_strength > 1
                RETURN suggested.name as name, labels(suggested)[0] as type, connection_strength
                ORDER BY connection_strength DESC
                LIMIT 10
            """)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Relationship suggestion failed: {e}")
            return []


# Enhanced MCP tool functions using the manager
async def enhanced_query_graph(cypher_query: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
    """Enhanced graph querying with better error handling."""
    kg_manager = KnowledgeGraphManager()
    
    try:
        results = await kg_manager.execute_cypher(cypher_query, parameters)
        
        return {
            "success": True,
            "query": cypher_query,
            "results": results,
            "count": len(results),
            "age_available": await kg_manager.check_age_availability()
        }
        
    except Exception as e:
        logger.error(f"Enhanced graph query failed: {e}")
        return {
            "success": False,
            "query": cypher_query,
            "error": str(e),
            "age_available": await kg_manager.check_age_availability()
        }


async def build_knowledge_graph_from_crawled_data(limit: int = 100) -> Dict[str, Any]:
    """Build knowledge graph from recently crawled documents."""
    kg_manager = KnowledgeGraphManager()
    return await kg_manager.build_graph_from_documents(limit)


async def analyze_knowledge_graph() -> Dict[str, Any]:
    """Perform advanced analysis on the knowledge graph."""
    kg_manager = KnowledgeGraphManager()
    return await kg_manager.analyze_graph_patterns()


async def get_entity_suggestions(entity_name: str) -> Dict[str, Any]:
    """Get suggestions for new relationships for an entity."""
    kg_manager = KnowledgeGraphManager()
    suggestions = await kg_manager.suggest_new_relationships(entity_name)
    
    return {
        "success": True,
        "entity": entity_name,
        "suggested_relationships": suggestions,
        "count": len(suggestions)
    }