# dealflow/knowledge_base/embeddings.py
from typing import List, Optional, Any

from camel.embeddings import OpenAIEmbedding, SentenceTransformerEncoder

from dealflow.exceptions import KnowledgeBaseError
from dealflow.utils.logger import logger

class EmbeddingAdapter:
    """Adapter for embedding models."""
    
    @staticmethod
    def create_embedding_model(
        embedding_type: str = "openai",
        model_name: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create an embedding model.
        
        Args:
            embedding_type: The type of embedding model to create.
            model_name: The name of the model to use (for SentenceTransformerEncoder).
            **kwargs: Additional arguments for model creation.
            
        Returns:
            An embedding model instance.
            
        Raises:
            KnowledgeBaseError: If the embedding model creation fails.
        """
        try:
            if embedding_type.lower() == "openai":
                logger.info("Creating OpenAI embedding model")
                return OpenAIEmbedding(**kwargs)
            elif embedding_type.lower() == "sentence_transformer":
                if not model_name:
                    model_name = 'intfloat/e5-large-v2'
                logger.info(f"Creating SentenceTransformer embedding model with name {model_name}")
                return SentenceTransformerEncoder(model_name=model_name, **kwargs)
            else:
                raise KnowledgeBaseError(f"Unsupported embedding type: {embedding_type}")
        except Exception as e:
            logger.error(f"Error creating embedding model: {e}")
            raise KnowledgeBaseError(f"Error creating embedding model: {e}")
    
    @staticmethod
    def embed_texts(
        embedding_model: Any,
        texts: List[str]
    ) -> List[List[float]]:
        """Embed a list of texts.
        
        Args:
            embedding_model: The embedding model to use.
            texts: The texts to embed.
            
        Returns:
            A list of embeddings, each embedding being a list of floats.
            
        Raises:
            KnowledgeBaseError: If the embedding fails.
        """
        try:
            return embedding_model.embed_list(texts)
        except Exception as e:
            logger.error(f"Error embedding texts: {e}")
            raise KnowledgeBaseError(f"Error embedding texts: {e}")