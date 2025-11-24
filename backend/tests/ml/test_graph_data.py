"""
Unit tests for GraphDataBuilder service.
"""
import pytest
import torch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.graph_data import GraphDataBuilder


class TestGraphDataBuilder:
    """Test graph data building from database."""

    @pytest.mark.asyncio
    async def test_build_empty_graph(self, db_session: AsyncSession):
        """Test building graph with no data returns empty graph."""
        builder = GraphDataBuilder(db_session)
        
        edge_index, metadata = await builder.build_graph(min_interactions=1)
        
        assert edge_index.shape == (2, 0) or edge_index.shape[1] == 0
        assert metadata["num_users"] == 0 or metadata["num_edges"] == 0

    @pytest.mark.asyncio
    async def test_id_mapping_consistency(self, db_session: AsyncSession):
        """Test ID mappings are consistent and reversible."""
        builder = GraphDataBuilder(db_session)
        
        # Build graph (may be empty, that's ok)
        await builder.build_graph(min_interactions=0)
        
        # Test user mappings
        for db_id, graph_idx in builder.user_id_to_idx.items():
            assert builder.get_user_id(graph_idx) == db_id
            assert builder.get_user_idx(db_id) == graph_idx
        
        # Test venue mappings
        for db_id, graph_idx in builder.venue_id_to_idx.items():
            assert builder.get_venue_id(graph_idx) == db_id
            assert builder.get_venue_idx(db_id) == graph_idx

    def test_get_user_idx_nonexistent(self):
        """Test getting index for non-existent user returns None."""
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        
        # Create minimal session (won't actually query)
        builder = GraphDataBuilder(None)  # type: ignore
        
        assert builder.get_user_idx(99999) is None
        assert builder.get_venue_idx(99999) is None

