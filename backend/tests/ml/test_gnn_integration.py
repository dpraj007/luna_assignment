"""
Integration tests for GNN training and recommendation integration.
"""
import pytest
import torch
from pathlib import Path
import tempfile
import shutil
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gnn_trainer import GNNTrainer
from app.services.recommendation import RecommendationEngine


class TestGNNIntegration:
    """Test GNN integration with recommendation engine."""

    @pytest.mark.asyncio
    async def test_trainer_initialization(self, db_session: AsyncSession):
        """Test GNNTrainer can be initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = GNNTrainer(
                db=db_session,
                model_dir=tmpdir,
                epochs=1  # Quick test
            )
            
            assert trainer.db == db_session
            assert trainer.model_dir == Path(tmpdir)
            assert trainer.model is None  # Not trained yet

    @pytest.mark.asyncio
    async def test_recommendation_engine_with_gnn(self, db_session: AsyncSession):
        """Test RecommendationEngine can be initialized with GNN trainer."""
        trainer = GNNTrainer(db=db_session)
        engine = RecommendationEngine(db=db_session, gnn_trainer=trainer)
        
        assert engine.db == db_session
        assert engine.gnn_trainer == trainer
        assert engine.use_gnn is True

    @pytest.mark.asyncio
    async def test_recommendation_engine_without_gnn(self, db_session: AsyncSession):
        """Test RecommendationEngine works without GNN trainer."""
        engine = RecommendationEngine(db=db_session)
        
        assert engine.db == db_session
        assert engine.gnn_trainer is None
        assert engine.use_gnn is False

    @pytest.mark.asyncio
    async def test_gnn_score_fallback(self, db_session: AsyncSession):
        """Test GNN score falls back gracefully when model not available."""
        trainer = GNNTrainer(db=db_session)
        engine = RecommendationEngine(db=db_session, gnn_trainer=trainer)
        
        # Should return neutral score when model not trained
        score = await engine._get_gnn_score(user_id=1, venue_id=1)
        assert 0 <= score <= 1
        assert score == 0.5  # Neutral fallback

