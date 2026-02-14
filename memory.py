"""
Semantic Memory with ChromaDB and Vector Embeddings.

This module implements a persistent semantic memory system that allows
the agent to learn from past actions, recall similar experiences, and
improve decision-making through contextual similarity search.

Architecture:
    - ChromaDB for persistent vector storage
    - sentence-transformers for semantic embeddings
    - Semantic Recall: agent queries historical actions before acting
    - Learning Loop: successful actions improve future decisions
"""

import asyncio
import hashlib
import json
from datetime import datetime
from typing import Any, Callable, Optional
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except ImportError:
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

from loguru import logger


class MemoryType(str, Enum):
    """Types of memory entries."""
    ACTION = "action"
    ERROR = "error"
    SUCCESS = "success"
    DECISION = "decision"
    OBSERVATION = "observation"


@dataclass
class MemoryEntry:
    """A single memory entry with semantic meaning."""
    id: str
    type: MemoryType
    content: str
    metadata: dict[str, Any]
    timestamp: str
    embedding: Optional[list[float]] = None
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['type'] = self.type.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary."""
        data['type'] = MemoryType(data['type'])
        return cls(**data)


class SemanticMemory:
    """
    Semantic memory system using ChromaDB and sentence-transformers.
    
    Provides:
    - Persistent vector storage of actions and memories
    - Semantic similarity search (find similar past actions)
    - Learning from successes and failures
    - Context-aware decision support
    """

    def __init__(
        self,
        db_path: str = "./.pyos/memory",
        model_name: str = "all-MiniLM-L6-v2",
        collection_name: str = "agent_memory",
    ):
        """
        Initialize semantic memory.
        
        Args:
            db_path: Path to ChromaDB persistence
            model_name: Sentence-transformer model for embeddings
            collection_name: ChromaDB collection name
        """
        if chromadb is None:
            logger.warning("ChromaDB not installed. Memory disabled.")
            self.enabled = False
            return

        self.enabled = True
        self.db_path = db_path
        self.model_name = model_name
        self.collection_name = collection_name

        # Initialize ChromaDB
        logger.info(f"Initializing SemanticMemory at {db_path}")
        try:
            self.client = chromadb.PersistentClient(
                path=db_path,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.enabled = False
            return

        # Initialize embeddings model
        if SentenceTransformer is None:
            logger.warning("sentence-transformers not installed. Using dummy embeddings.")
            self.embedder: Optional[SentenceTransformer] = None
        else:
            try:
                logger.info(f"Loading embeddings model: {model_name}")
                self.embedder = SentenceTransformer(model_name)
            except Exception as e:
                logger.error(f"Failed to load embeddings model: {e}")
                self.embedder = None

        self.entry_count = 0
        logger.info(f"SemanticMemory initialized with {self._count_entries()} existing entries")

    def _count_entries(self) -> int:
        """Count total entries in memory."""
        if not self.enabled:
            return 0
        try:
            return self.collection.count()
        except Exception:
            return 0

    def _embed(self, text: str) -> Optional[list[float]]:
        """Generate embedding for text."""
        if not self.embedder:
            # Return dummy embedding if model not available
            return [0.0] * 384

        try:
            embedding = self.embedder.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return None

    def _generate_id(self, content: str, timestamp: str) -> str:
        """Generate unique ID for memory entry."""
        combined = f"{content}{timestamp}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]

    async def store(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.ACTION,
        metadata: Optional[dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> MemoryEntry:
        """
        Store a memory entry.
        
        Args:
            content: The memory content (action, decision, observation)
            memory_type: Type of memory
            metadata: Additional context metadata
            success: Whether the action/decision succeeded
            error_message: Error details if failed
            
        Returns:
            Created MemoryEntry
        """
        if not self.enabled:
            return MemoryEntry(
                id="disabled",
                type=memory_type,
                content=content,
                metadata=metadata or {},
                timestamp=datetime.now().isoformat(),
            )

        timestamp = datetime.now().isoformat()
        entry_id = self._generate_id(content, timestamp)
        embedding = self._embed(content)

        entry = MemoryEntry(
            id=entry_id,
            type=memory_type,
            content=content,
            metadata=metadata or {},
            timestamp=timestamp,
            embedding=embedding,
            success=success,
            error_message=error_message,
        )

        try:
            self.collection.add(
                ids=[entry_id],
                documents=[content],
                embeddings=[embedding] if embedding else None,
                metadatas=[{
                    "type": memory_type.value,
                    "success": success,
                    "error": error_message or "",
                    "timestamp": timestamp,
                    **metadata
                }]
            )
            self.entry_count += 1
            logger.debug(f"Memory stored: {entry_id} ({memory_type.value})")
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")

        return entry

    async def recall(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[MemoryType] = None,
        success_only: bool = False,
    ) -> list[MemoryEntry]:
        """
        Recall similar memories using semantic search.
        
        Args:
            query: Semantic query (similar to past memories)
            limit: Max results to return
            memory_type: Filter by memory type
            success_only: Only return successful actions
            
        Returns:
            List of similar MemoryEntry objects, ordered by relevance
        """
        if not self.enabled:
            return []

        embedding = self._embed(query)
        if not embedding:
            return []

        try:
            # Build where filter if needed
            where_filter = None
            if memory_type or success_only:
                filters = []
                if memory_type:
                    filters.append({"type": {"$eq": memory_type.value}})
                if success_only:
                    filters.append({"success": {"$eq": True}})
                
                where_filter = {"$and": filters} if len(filters) > 1 else filters[0]

            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=limit,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )

            memories = []
            if results and results["ids"] and len(results["ids"]) > 0:
                for i, entry_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    document = results["documents"][0][i]

                    memory = MemoryEntry(
                        id=entry_id,
                        type=MemoryType(metadata.get("type", "action")),
                        content=document,
                        metadata={k: v for k, v in metadata.items() if k not in ["type", "success", "error", "timestamp"]},
                        timestamp=metadata.get("timestamp", datetime.now().isoformat()),
                        success=metadata.get("success", True),
                        error_message=metadata.get("error"),
                    )
                    memories.append(memory)

            logger.debug(f"Recalled {len(memories)} memories for query: {query[:50]}...")
            return memories

        except Exception as e:
            logger.error(f"Recall failed: {e}")
            return []

    async def learn_from_success(
        self,
        action: str,
        result: str,
        tool: str,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Store a successful action for future learning.
        
        Args:
            action: The action that succeeded
            result: The result/outcome
            tool: Tool that was used
            context: Additional context
        """
        metadata = {"tool": tool, "result": result, **(context or {})}
        await self.store(
            content=f"{action} → {result}",
            memory_type=MemoryType.SUCCESS,
            metadata=metadata,
            success=True,
        )

    async def learn_from_error(
        self,
        action: str,
        error: str,
        tool: str,
        attempted_fixes: Optional[list[str]] = None,
    ) -> None:
        """
        Store a failed action for learning and recovery.
        
        Args:
            action: The action that failed
            error: Error message
            tool: Tool that failed
            attempted_fixes: Fixes that were already tried
        """
        metadata = {
            "tool": tool,
            "attempted_fixes": attempted_fixes or [],
        }
        await self.store(
            content=f"ERROR: {action} failed",
            memory_type=MemoryType.ERROR,
            metadata=metadata,
            success=False,
            error_message=error,
        )

    async def get_similar_successes(self, action: str, limit: int = 3) -> list[MemoryEntry]:
        """Get successful past actions similar to the given action."""
        return await self.recall(
            query=action,
            limit=limit,
            memory_type=MemoryType.SUCCESS,
            success_only=True,
        )

    async def get_similar_errors(self, action: str, limit: int = 3) -> list[MemoryEntry]:
        """Get failed past actions similar to the given action."""
        return await self.recall(
            query=action,
            limit=limit,
            memory_type=MemoryType.ERROR,
            success_only=False,
        )

    def clear_memory(self) -> None:
        """Clear all memory entries. Use with caution!"""
        if not self.enabled:
            return
        
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.entry_count = 0
            logger.warning("Memory cleared!")
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")

    def export_memory(self, path: str) -> None:
        """Export all memories to JSON file."""
        if not self.enabled:
            return

        try:
            all_entries = self.collection.get(include=["documents", "metadatas"])
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "total_entries": len(all_entries["ids"]),
                "entries": []
            }

            for i, entry_id in enumerate(all_entries["ids"]):
                export_data["entries"].append({
                    "id": entry_id,
                    "document": all_entries["documents"][i],
                    "metadata": all_entries["metadatas"][i],
                })

            with open(path, "w") as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Memory exported to {path}")
        except Exception as e:
            logger.error(f"Export failed: {e}")

    def stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        if not self.enabled:
            return {"enabled": False}

        return {
            "enabled": True,
            "total_entries": self._count_entries(),
            "collection": self.collection_name,
            "model": self.model_name,
            "db_path": self.db_path,
        }
