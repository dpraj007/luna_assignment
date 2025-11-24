"""
LightGCN (Light Graph Convolutional Network) for venue recommendations.

LightGCN is a simplified GCN that removes feature transformation and non-linear activation,
focusing purely on neighborhood aggregation. It's state-of-the-art for collaborative filtering.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class LightGCN(nn.Module):
    """
    LightGCN model for bipartite graph recommendation.
    
    Architecture:
    - Embedding layer for users and venues
    - Multiple graph convolution layers (neighborhood aggregation)
    - Final embeddings are average of all layer embeddings
    - Prediction: dot product of user and venue embeddings
    """

    def __init__(
        self,
        num_users: int,
        num_venues: int,
        embedding_dim: int = 64,
        num_layers: int = 3,
        dropout: float = 0.0
    ):
        """
        Initialize LightGCN model.
        
        Args:
            num_users: Number of users in the graph
            num_venues: Number of venues in the graph
            embedding_dim: Dimension of user/venue embeddings
            num_layers: Number of graph convolution layers
            dropout: Dropout rate (0.0 = no dropout)
        """
        super(LightGCN, self).__init__()
        
        self.num_users = num_users
        self.num_venues = num_venues
        self.num_nodes = num_users + num_venues
        self.embedding_dim = embedding_dim
        self.num_layers = num_layers
        self.dropout = dropout
        
        # Initialize embeddings
        # Users: [0, num_users)
        # Venues: [num_users, num_users + num_venues)
        self.embedding = nn.Embedding(self.num_nodes, embedding_dim)
        
        # Initialize with small random values
        nn.init.normal_(self.embedding.weight, std=0.1)
        
        logger.info(
            f"Initialized LightGCN: {num_users} users, {num_venues} venues, "
            f"embedding_dim={embedding_dim}, layers={num_layers}"
        )

    def forward(
        self,
        edge_index: torch.Tensor,
        user_indices: Optional[torch.Tensor] = None,
        venue_indices: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through LightGCN.
        
        Args:
            edge_index: Graph edge index tensor [2, num_edges]
            user_indices: Optional user indices to get embeddings for (if None, returns all)
            venue_indices: Optional venue indices to get embeddings for (if None, returns all)
        
        Returns:
            Tuple of (user_embeddings, venue_embeddings)
            If user_indices/venue_indices provided, returns only those embeddings
        """
        # Get initial embeddings for all nodes
        all_embeddings = self.embedding.weight
        
        # Store embeddings from each layer
        embeddings_list = [all_embeddings]
        
        # Graph convolution layers
        for layer_idx in range(self.num_layers):
            # LightGCN: simple neighborhood aggregation without transformation
            # For each node, aggregate embeddings from neighbors
            
            # Build adjacency matrix multiplication
            # In LightGCN, we normalize by sqrt(degree) for both source and target
            neighbor_embeddings = self._propagate(edge_index, all_embeddings)
            
            # Average with previous layer (residual-like, but LightGCN uses simple aggregation)
            all_embeddings = neighbor_embeddings
            
            # Apply dropout
            if self.dropout > 0:
                all_embeddings = F.dropout(all_embeddings, p=self.dropout, training=self.training)
            
            embeddings_list.append(all_embeddings)
        
        # Final embeddings: average of all layers (including initial)
        final_embeddings = torch.stack(embeddings_list, dim=0).mean(dim=0)
        
        # Split into user and venue embeddings
        user_embeddings = final_embeddings[:self.num_users]
        venue_embeddings = final_embeddings[self.num_users:]
        
        # If specific indices requested, return only those
        if user_indices is not None:
            user_embeddings = user_embeddings[user_indices]
        if venue_indices is not None:
            venue_embeddings = venue_embeddings[venue_indices]
        
        return user_embeddings, venue_embeddings

    def _propagate(self, edge_index: torch.Tensor, embeddings: torch.Tensor) -> torch.Tensor:
        """
        Propagate embeddings through graph edges.
        
        LightGCN uses symmetric normalization: 1 / sqrt(degree_i * degree_j)
        Uses efficient scatter operations for aggregation.
        """
        # Get source and target nodes
        row, col = edge_index
        
        # Calculate degrees for normalization (count edges for each node)
        deg = torch.zeros(self.num_nodes, dtype=torch.float32, device=embeddings.device)
        deg = deg.scatter_add_(0, row, torch.ones(row.size(0), device=embeddings.device))
        deg = deg.scatter_add_(0, col, torch.ones(col.size(0), device=embeddings.device))
        
        # Avoid division by zero
        deg = torch.clamp(deg, min=1.0)
        deg_inv_sqrt = deg.pow(-0.5)
        deg_inv_sqrt[deg_inv_sqrt == float('inf')] = 0
        
        # Normalize edge weights: symmetric normalization
        norm = deg_inv_sqrt[row] * deg_inv_sqrt[col]
        
        # Efficient aggregation: for each source node, aggregate weighted neighbor embeddings
        # Weight neighbor embeddings by normalization factor
        weighted_embeddings = embeddings[col] * norm.unsqueeze(1)  # [num_edges, embedding_dim]
        
        # Aggregate using scatter_add: sum weighted embeddings for each target node
        neighbor_embeddings = torch.zeros_like(embeddings)
        neighbor_embeddings = neighbor_embeddings.scatter_add_(
            0,
            row.unsqueeze(1).expand(-1, embeddings.size(1)),
            weighted_embeddings
        )
        
        return neighbor_embeddings

    def predict(self, user_idx: int, venue_indices: torch.Tensor) -> torch.Tensor:
        """
        Predict affinity scores for a user and multiple venues.
        
        Args:
            user_idx: User graph index
            venue_indices: Tensor of venue graph indices
        
        Returns:
            Tensor of affinity scores
        """
        self.eval()
        with torch.no_grad():
            # Get embeddings (need edge_index, but we'll use cached if available)
            # For prediction, we typically use pre-computed embeddings
            # This is a simplified version - in practice, embeddings would be cached
            user_emb = self.embedding.weight[user_idx]
            venue_embs = self.embedding.weight[self.num_users:][venue_indices]
            
            # Dot product for affinity
            scores = torch.matmul(venue_embs, user_emb)
            return scores

    def get_all_embeddings(self, edge_index: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Get embeddings for all users and venues."""
        return self.forward(edge_index)


def bpr_loss(
    user_embeddings: torch.Tensor,
    venue_embeddings: torch.Tensor,
    positive_pairs: torch.Tensor,
    negative_pairs: torch.Tensor
) -> torch.Tensor:
    """
    Bayesian Personalized Ranking (BPR) Loss.
    
    Optimizes: log(sigmoid(score(positive) - score(negative)))
    
    Args:
        user_embeddings: User embeddings [batch_size, embedding_dim]
        venue_embeddings: Venue embeddings [num_venues, embedding_dim]
        positive_pairs: Positive (user_idx, venue_idx) pairs [batch_size, 2]
        negative_pairs: Negative (user_idx, venue_idx) pairs [batch_size, 2]
    
    Returns:
        BPR loss scalar
    """
    # Get embeddings for positive pairs
    pos_user_embs = user_embeddings[positive_pairs[:, 0]]
    pos_venue_embs = venue_embeddings[positive_pairs[:, 1]]
    pos_scores = (pos_user_embs * pos_venue_embs).sum(dim=1)
    
    # Get embeddings for negative pairs
    neg_user_embs = user_embeddings[negative_pairs[:, 0]]
    neg_venue_embs = venue_embeddings[negative_pairs[:, 1]]
    neg_scores = (neg_user_embs * neg_venue_embs).sum(dim=1)
    
    # BPR loss: -log(sigmoid(pos_score - neg_score))
    loss = -torch.log(torch.sigmoid(pos_scores - neg_scores) + 1e-10).mean()
    
    return loss

