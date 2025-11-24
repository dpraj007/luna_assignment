"""
Unit tests for LightGCN model.
"""
import pytest
import torch
from app.ml_models.lightgcn import LightGCN, bpr_loss


class TestLightGCN:
    """Test LightGCN model architecture."""

    def test_model_initialization(self):
        """Test model can be initialized with correct dimensions."""
        num_users = 10
        num_venues = 20
        embedding_dim = 64
        num_layers = 3
        
        model = LightGCN(
            num_users=num_users,
            num_venues=num_venues,
            embedding_dim=embedding_dim,
            num_layers=num_layers
        )
        
        assert model.num_users == num_users
        assert model.num_venues == num_venues
        assert model.num_nodes == num_users + num_venues
        assert model.embedding_dim == embedding_dim
        assert model.num_layers == num_layers
        assert model.embedding.weight.shape == (num_users + num_venues, embedding_dim)

    def test_forward_pass(self):
        """Test forward pass produces correct output shapes."""
        num_users = 5
        num_venues = 10
        embedding_dim = 32
        
        model = LightGCN(
            num_users=num_users,
            num_venues=num_venues,
            embedding_dim=embedding_dim,
            num_layers=2
        )
        
        # Create dummy edge index (some user-venue edges)
        edge_index = torch.tensor([
            [0, 1, 2, 0, 1],  # User indices
            [5, 6, 7, 8, 9]   # Venue indices (offset by num_users)
        ], dtype=torch.long)
        
        user_embeddings, venue_embeddings = model.forward(edge_index)
        
        assert user_embeddings.shape == (num_users, embedding_dim)
        assert venue_embeddings.shape == (num_venues, embedding_dim)

    def test_forward_pass_with_indices(self):
        """Test forward pass with specific user/venue indices."""
        num_users = 10
        num_venues = 20
        embedding_dim = 64
        
        model = LightGCN(
            num_users=num_users,
            num_venues=num_venues,
            embedding_dim=embedding_dim
        )
        
        edge_index = torch.tensor([
            [0, 1, 2],
            [10, 11, 12]
        ], dtype=torch.long)
        
        user_indices = torch.tensor([0, 1])
        venue_indices = torch.tensor([0, 1])
        
        user_embeddings, venue_embeddings = model.forward(
            edge_index,
            user_indices=user_indices,
            venue_indices=venue_indices
        )
        
        assert user_embeddings.shape == (2, embedding_dim)
        assert venue_embeddings.shape == (2, embedding_dim)

    def test_predict_method(self):
        """Test prediction method produces scores."""
        num_users = 5
        num_venues = 10
        embedding_dim = 32
        
        model = LightGCN(
            num_users=num_users,
            num_venues=num_venues,
            embedding_dim=embedding_dim
        )
        
        user_idx = 0
        venue_indices = torch.tensor([0, 1, 2])
        
        scores = model.predict(user_idx, venue_indices)
        
        assert scores.shape == (3,)
        assert torch.all(torch.isfinite(scores))


class TestBPRLoss:
    """Test BPR loss function."""

    def test_bpr_loss_shape(self):
        """Test BPR loss produces scalar output."""
        batch_size = 10
        embedding_dim = 64
        
        user_embeddings = torch.randn(batch_size, embedding_dim)
        venue_embeddings = torch.randn(20, embedding_dim)
        
        positive_pairs = torch.randint(0, batch_size, (batch_size, 2))
        positive_pairs[:, 1] = torch.randint(0, 20, (batch_size,))
        
        negative_pairs = torch.randint(0, batch_size, (batch_size, 2))
        negative_pairs[:, 1] = torch.randint(0, 20, (batch_size,))
        
        loss = bpr_loss(
            user_embeddings,
            venue_embeddings,
            positive_pairs,
            negative_pairs
        )
        
        assert loss.shape == ()
        assert torch.isfinite(loss)
        assert loss.item() > 0  # Loss should be positive

    def test_bpr_loss_decreases_with_better_predictions(self):
        """Test that BPR loss decreases when positive scores are higher."""
        embedding_dim = 32
        
        # Create embeddings where positive pairs are more similar
        user_emb = torch.randn(1, embedding_dim)
        pos_venue_emb = user_emb + 0.1 * torch.randn(1, embedding_dim)  # Similar
        neg_venue_emb = -user_emb + 0.1 * torch.randn(1, embedding_dim)  # Dissimilar
        
        venue_embs = torch.cat([pos_venue_emb, neg_venue_emb], dim=0)
        
        positive_pairs = torch.tensor([[0, 0]])
        negative_pairs = torch.tensor([[0, 1]])
        
        loss = bpr_loss(
            user_emb,
            venue_embs,
            positive_pairs,
            negative_pairs
        )
        
        # Loss should be relatively low when positive > negative
        assert loss.item() < 1.0

