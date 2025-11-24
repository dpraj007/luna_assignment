"""
GNN Training Service: Manages training lifecycle for LightGCN model.
"""
import os
import json
import logging
from typing import Optional, Dict, Tuple
from pathlib import Path
import torch
import torch.optim as optim
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from ..ml_models.lightgcn import LightGCN, bpr_loss
from .graph_data import GraphDataBuilder

logger = logging.getLogger(__name__)


class GNNTrainer:
    """
    Service for training and managing the LightGCN recommendation model.
    """

    def __init__(
        self,
        db: AsyncSession,
        model_dir: str = "./models",
        embedding_dim: int = 64,
        num_layers: int = 3,
        learning_rate: float = 0.001,
        batch_size: int = 2048,
        epochs: int = 100
    ):
        """
        Initialize GNN trainer.
        
        Args:
            db: Database session
            model_dir: Directory to save/load models
            embedding_dim: Embedding dimension
            num_layers: Number of GCN layers
            learning_rate: Learning rate for optimizer
            batch_size: Batch size for training
            epochs: Number of training epochs
        """
        self.db = db
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.embedding_dim = embedding_dim
        self.num_layers = num_layers
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        
        self.model: Optional[LightGCN] = None
        self.edge_index: Optional[torch.Tensor] = None
        self.metadata: Optional[Dict] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        logger.info(f"GNN Trainer initialized. Device: {self.device}")

    async def train(
        self,
        min_interactions: int = 1,
        include_friendships: bool = True,
        save_model: bool = True
    ) -> Dict:
        """
        Train the LightGCN model.
        
        Args:
            min_interactions: Minimum interactions to include user/venue
            include_friendships: Whether to include friendship edges
            save_model: Whether to save trained model
        
        Returns:
            Training metrics dictionary
        """
        logger.info("Starting GNN training...")
        
        # Step 1: Build graph from database
        logger.info("Building graph from database...")
        graph_builder = GraphDataBuilder(self.db)
        edge_index, metadata = await graph_builder.build_graph(
            min_interactions=min_interactions,
            include_friendships=include_friendships
        )
        
        if edge_index.shape[1] == 0:
            raise ValueError("No edges found in graph. Cannot train model.")
        
        self.edge_index = edge_index.to(self.device)
        self.metadata = metadata
        
        num_users = metadata["num_users"]
        num_venues = metadata["num_venues"]
        
        logger.info(f"Graph built: {num_users} users, {num_venues} venues, {edge_index.shape[1]} edges")
        
        # Step 2: Initialize model
        self.model = LightGCN(
            num_users=num_users,
            num_venues=num_venues,
            embedding_dim=self.embedding_dim,
            num_layers=self.num_layers
        ).to(self.device)
        
        # Step 3: Prepare training data (positive and negative pairs)
        logger.info("Preparing training data...")
        positive_pairs, negative_pairs = self._prepare_training_pairs(edge_index, num_users, num_venues)
        
        if len(positive_pairs) == 0:
            raise ValueError("No positive pairs found. Cannot train model.")
        
        logger.info(f"Prepared {len(positive_pairs)} positive pairs")
        
        # Step 4: Train model
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        losses = []
        best_loss = float('inf')
        
        logger.info(f"Training for {self.epochs} epochs...")
        
        for epoch in range(self.epochs):
            self.model.train()
            epoch_losses = []
            
            # Shuffle training pairs
            indices = torch.randperm(len(positive_pairs))
            positive_pairs_shuffled = positive_pairs[indices]
            negative_pairs_shuffled = negative_pairs[indices]
            
            # Mini-batch training
            num_batches = (len(positive_pairs) + self.batch_size - 1) // self.batch_size
            
            for batch_idx in range(num_batches):
                start_idx = batch_idx * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(positive_pairs))
                
                batch_pos = positive_pairs_shuffled[start_idx:end_idx]
                batch_neg = negative_pairs_shuffled[start_idx:end_idx]
                
                # Forward pass
                user_embeddings, venue_embeddings = self.model.forward(self.edge_index)
                
                # Calculate BPR loss
                loss = bpr_loss(
                    user_embeddings,
                    venue_embeddings,
                    batch_pos,
                    batch_neg
                )
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_losses.append(loss.item())
            
            avg_loss = np.mean(epoch_losses)
            losses.append(avg_loss)
            
            if avg_loss < best_loss:
                best_loss = avg_loss
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch + 1}/{self.epochs}, Loss: {avg_loss:.4f}")
        
        logger.info(f"Training completed. Best loss: {best_loss:.4f}")
        
        # Step 5: Save model
        if save_model:
            await self.save_model()
        
        # Store metadata for later use
        self.metadata = metadata
        
        return {
            "success": True,
            "num_users": num_users,
            "num_venues": num_venues,
            "num_edges": edge_index.shape[1],
            "epochs": self.epochs,
            "final_loss": losses[-1],
            "best_loss": best_loss,
            "losses": losses,
            "model_path": str(self.model_dir / "lightgcn.pt") if save_model else None
        }

    def _prepare_training_pairs(
        self,
        edge_index: torch.Tensor,
        num_users: int,
        num_venues: int
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Prepare positive and negative training pairs.
        
        Positive pairs: (user_idx, venue_idx) from actual interactions
        Negative pairs: (user_idx, random_venue_idx) where no interaction exists
        """
        # Extract user-venue edges (exclude user-user edges)
        # User nodes: [0, num_users), Venue nodes: [num_users, num_users + num_venues)
        user_mask = edge_index[0] < num_users
        venue_mask = edge_index[1] >= num_users
        user_venue_mask = user_mask & venue_mask
        user_venue_edges = edge_index[:, user_venue_mask]
        
        if user_venue_edges.shape[1] == 0:
            return torch.empty((0, 2), dtype=torch.long, device=edge_index.device), \
                   torch.empty((0, 2), dtype=torch.long, device=edge_index.device)
        
        # Get user and venue indices
        user_indices = user_venue_edges[0]  # Already in [0, num_users)
        venue_indices = user_venue_edges[1] - num_users  # Convert to venue index [0, num_venues)
        
        # Ensure indices are valid
        assert torch.all(user_indices >= 0) and torch.all(user_indices < num_users), \
            f"Invalid user indices: min={user_indices.min()}, max={user_indices.max()}, num_users={num_users}"
        assert torch.all(venue_indices >= 0) and torch.all(venue_indices < num_venues), \
            f"Invalid venue indices: min={venue_indices.min()}, max={venue_indices.max()}, num_venues={num_venues}"
        
        # Create positive pairs
        positive_pairs = torch.stack([user_indices, venue_indices], dim=1)
        
        # Create negative pairs: sample random venues for each user
        negative_venue_indices = torch.randint(0, num_venues, (len(positive_pairs),), device=edge_index.device)
        negative_pairs = torch.stack([user_indices, negative_venue_indices], dim=1)
        
        # Filter out negative pairs that are actually positive (collision)
        # Simple approach: just resample if collision (for now)
        # In production, you'd want a more sophisticated negative sampling strategy
        
        return positive_pairs, negative_pairs

    async def save_model(self):
        """Save trained model and metadata."""
        if self.model is None:
            raise ValueError("No model to save. Train model first.")
        
        model_path = self.model_dir / "lightgcn.pt"
        metadata_path = self.model_dir / "gnn_metadata.json"
        
        # Save model state
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "embedding_dim": self.embedding_dim,
            "num_layers": self.num_layers,
            "num_users": self.metadata["num_users"],
            "num_venues": self.metadata["num_venues"],
        }, model_path)
        
        # Save metadata (ID mappings)
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        logger.info(f"Model saved to {model_path}")
        logger.info(f"Metadata saved to {metadata_path}")

    async def load_model(self, rebuild_graph: bool = True) -> bool:
        """
        Load trained model from disk.
        
        Args:
            rebuild_graph: Whether to rebuild edge_index from database (default: True)
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        model_path = self.model_dir / "lightgcn.pt"
        metadata_path = self.model_dir / "gnn_metadata.json"
        
        if not model_path.exists() or not metadata_path.exists():
            logger.warning("Model files not found. Train model first.")
            return False
        
        try:
            # Load metadata
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
            
            # Load model state
            checkpoint = torch.load(model_path, map_location=self.device)
            
            num_users = checkpoint["num_users"]
            num_venues = checkpoint["num_venues"]
            embedding_dim = checkpoint["embedding_dim"]
            num_layers = checkpoint["num_layers"]
            
            # Initialize model
            self.model = LightGCN(
                num_users=num_users,
                num_venues=num_venues,
                embedding_dim=embedding_dim,
                num_layers=num_layers
            ).to(self.device)
            
            # Load weights
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.model.eval()
            
            # Rebuild edge_index from database if requested
            if rebuild_graph:
                logger.info("Rebuilding graph from database...")
                graph_builder = GraphDataBuilder(self.db)
                edge_index, _ = await graph_builder.build_graph(
                    min_interactions=1,
                    include_friendships=True
                )
                if edge_index.shape[1] > 0:
                    self.edge_index = edge_index.to(self.device)
                    logger.info(f"Graph rebuilt: {edge_index.shape[1]} edges")
                else:
                    logger.warning("No edges found when rebuilding graph")
            
            logger.info("Model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}", exc_info=True)
            return False

    def get_user_embeddings(self, user_indices: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Get embeddings for users."""
        if self.model is None or self.edge_index is None:
            raise ValueError("Model not trained or graph not built. Train model first.")
        
        self.model.eval()
        with torch.no_grad():
            user_embeddings, _ = self.model.forward(self.edge_index, user_indices=user_indices)
            return user_embeddings

    def get_venue_embeddings(self, venue_indices: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Get embeddings for venues."""
        if self.model is None or self.edge_index is None:
            raise ValueError("Model not trained or graph not built. Train model first.")
        
        self.model.eval()
        with torch.no_grad():
            _, venue_embeddings = self.model.forward(self.edge_index, venue_indices=venue_indices)
            return venue_embeddings

    def predict_user_venue_scores(
        self,
        user_idx: int,
        venue_indices: torch.Tensor
    ) -> torch.Tensor:
        """
        Predict affinity scores for a user and venues.
        
        Args:
            user_idx: User graph index
            venue_indices: Tensor of venue graph indices
        
        Returns:
            Tensor of scores
        """
        if self.model is None:
            raise ValueError("Model not trained. Train model first.")
        
        if self.edge_index is None:
            raise ValueError("Edge index not available. Rebuild graph or train model first.")
        
        # Validate indices
        if user_idx < 0 or user_idx >= self.model.num_users:
            raise ValueError(f"Invalid user_idx {user_idx}, must be in [0, {self.model.num_users})")
        
        if venue_indices.numel() > 0:
            if venue_indices.min() < 0 or venue_indices.max() >= self.model.num_venues:
                raise ValueError(
                    f"Invalid venue_indices, must be in [0, {self.model.num_venues}), "
                    f"got min={venue_indices.min()}, max={venue_indices.max()}"
                )
        
        user_embeddings = self.get_user_embeddings(torch.tensor([user_idx], device=self.device))
        venue_embeddings = self.get_venue_embeddings(venue_indices)
        
        # Dot product for affinity
        scores = torch.matmul(venue_embeddings, user_embeddings[0])
        return scores

