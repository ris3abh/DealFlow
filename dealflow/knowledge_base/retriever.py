# dealflow/knowledge_base/retriever.py
from typing import List, Dict, Any, Optional, Tuple, Union

from camel.retrievers import VectorRetriever
from camel.storages import QdrantStorage, VectorRecord
from camel.embeddings import OpenAIEmbedding

from dealflow.knowledge_base.embeddings import EmbeddingAdapter
from dealflow.knowledge_base.loader import EntityKnowledgeLoader
from dealflow.exceptions import KnowledgeBaseError
from dealflow.utils.logger import logger
from dealflow.schemas.entity import Entity, EntityType

class EntityKnowledgeRetriever:
    """Retriever for entity knowledge (products, services, appointments, etc.)."""
    
    def __init__(
        self,
        embedding_model: Any = None,
        vector_storage: Any = None,
        collection_name: str = "entity_knowledge",
        embedding_type: str = "openai",
        vector_dim: Optional[int] = None,
    ):
        """Initialize the entity knowledge retriever.
        
        Args:
            embedding_model: The embedding model to use. If None, a new one will be created.
            vector_storage: The vector storage to use. If None, a new one will be created.
            collection_name: The name of the collection in the vector storage.
            embedding_type: The type of embedding model to create if embedding_model is None.
            vector_dim: The dimension of the vectors. If None, it will be retrieved from the embedding model.
        """
        # Initialize embedding model
        self.embedding_model = embedding_model or EmbeddingAdapter.create_embedding_model(
            embedding_type=embedding_type
        )
        
        # Get vector dimension
        if vector_dim is None:
            try:
                vector_dim = self.embedding_model.get_output_dim()
            except AttributeError:
                # Default for OpenAI embeddings
                vector_dim = 1536
                logger.warning(f"Could not determine vector dimension, using default: {vector_dim}")
        
        # Initialize vector storage
        self.vector_storage = vector_storage or QdrantStorage(
            vector_dim=vector_dim,
            collection_name=collection_name,
        )
        
        # Initialize retriever
        self.retriever = VectorRetriever(embedding_model=self.embedding_model)
        
        logger.info(f"Initialized entity knowledge retriever with collection '{collection_name}'")
    
    def add_content(self, content: str) -> None:
        """Add content to the retriever.
        
        Args:
            content: The content to add.
        """
        try:
            self.retriever.process(content, self.vector_storage)
            logger.info("Added content to retriever")
        except Exception as e:
            logger.error(f"Error adding content to retriever: {e}")
            raise KnowledgeBaseError(f"Error adding content to retriever: {e}")
    
    def load_from_file(self, file_path: str) -> None:
        """Load content from a file and add it to the retriever.
        
        Args:
            file_path: The path to the file.
        """
        try:
            content = EntityKnowledgeLoader.load_from_text(file_path)
            self.add_content(content)
            logger.info(f"Loaded content from {file_path}")
        except Exception as e:
            logger.error(f"Error loading content from {file_path}: {e}")
            raise KnowledgeBaseError(f"Error loading content from {file_path}: {e}")
    
    def query(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Query the entity knowledge.
        
        Args:
            query: The query to search for.
            top_k: The number of top results to return.
            
        Returns:
            A list of results, each containing the text and metadata.
        """
        try:
            results = self.retriever.query(query, self.vector_storage, top_k=top_k)
            logger.debug(f"Query: '{query}' returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error querying entity knowledge: {e}")
            raise KnowledgeBaseError(f"Error querying entity knowledge: {e}")
    
    def add_entity(self, entity: Union[Entity, Dict[str, Any]]) -> None:
        """Add an entity to the retriever.
        
        Args:
            entity: The entity to add (either an Entity object or a dictionary).
        """
        try:
            # Convert dictionary to Entity if needed
            if isinstance(entity, dict):
                entity = Entity.from_dict(entity)
            
            # Format entity information as text
            entity_text = entity.format_for_display()
            
            # Add to vector storage
            self.add_content(entity_text)
            logger.info(f"Added entity {entity.name} to retriever")
        except Exception as e:
            logger.error(f"Error adding entity to retriever: {e}")
            raise KnowledgeBaseError(f"Error adding entity to retriever: {e}")
    
    def batch_add_entities(self, entities: List[Union[Entity, Dict[str, Any]]]) -> None:
        """Add multiple entities to the retriever.
        
        Args:
            entities: A list of entities to add.
        """
        try:
            combined_content = ""
            
            for entity in entities:
                # Convert dictionary to Entity if needed
                if isinstance(entity, dict):
                    entity = Entity.from_dict(entity)
                
                # Format entity information as text
                entity_text = entity.format_for_display()
                combined_content += entity_text + "\n\n"
            
            # Add to vector storage
            if combined_content:
                self.add_content(combined_content)
                logger.info(f"Added {len(entities)} entities to retriever")
        except Exception as e:
            logger.error(f"Error batch adding entities to retriever: {e}")
            raise KnowledgeBaseError(f"Error batch adding entities to retriever: {e}")
    
    def clear(self) -> None:
        """Clear the entity knowledge."""
        try:
            self.vector_storage.clear()
            logger.info("Cleared entity knowledge")
        except Exception as e:
            logger.error(f"Error clearing entity knowledge: {e}")
            raise KnowledgeBaseError(f"Error clearing entity knowledge: {e}")