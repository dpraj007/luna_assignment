"""
Graph Data Service: Converts SQL relational data into graph tensors for GNN training.

This service builds bipartite graphs:
- User-Venue edges from interactions (views, saves, bookings, interests)
- User-User edges from friendships
"""
from typing import Dict, List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import torch
import numpy as np
import logging

from ..models.user import User, Friendship
from ..models.venue import Venue
from ..models.interaction import UserInteraction, InteractionType, VenueInterest
from ..models.booking import Booking

logger = logging.getLogger(__name__)


class GraphDataBuilder:
    """
    Builds graph tensors from database relationships.
    
    Creates mappings from Database IDs to Graph Indices:
    - Users: [0, num_users)
    - Venues: [num_users, num_users + num_venues)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_id_to_idx: Dict[int, int] = {}
        self.venue_id_to_idx: Dict[int, int] = {}
        self.idx_to_user_id: Dict[int, int] = {}
        self.idx_to_venue_id: Dict[int, int] = {}
        self.num_users: int = 0
        self.num_venues: int = 0

    async def build_graph(
        self,
        min_interactions: int = 1,
        include_friendships: bool = True
    ) -> Tuple[torch.Tensor, Dict]:
        """
        Build the complete graph from database.
        
        Args:
            min_interactions: Minimum number of interactions for a user/venue to be included
            include_friendships: Whether to include user-user friendship edges
        
        Returns:
            Tuple of (edge_index tensor, metadata dict)
            edge_index shape: [2, num_edges]
            metadata contains:
                - num_users, num_venues
                - id_mappings (for converting back to DB IDs)
        """
        # Step 1: Build ID mappings
        await self._build_id_mappings(min_interactions)
        
        if self.num_users == 0 or self.num_venues == 0:
            logger.warning("No users or venues found. Returning empty graph.")
            return torch.empty((2, 0), dtype=torch.long), {
                "num_users": 0,
                "num_venues": 0,
                "num_edges": 0
            }
        
        # Step 2: Build User-Venue edges (interactions)
        user_venue_edges = await self._build_user_venue_edges()
        
        # Step 3: Build User-User edges (friendships) if requested
        user_user_edges = []
        if include_friendships:
            user_user_edges = await self._build_user_user_edges()
        
        # Step 4: Combine all edges
        all_edges = user_venue_edges + user_user_edges
        
        if len(all_edges) == 0:
            logger.warning("No edges found. Returning empty graph.")
            return torch.empty((2, 0), dtype=torch.long), {
                "num_users": self.num_users,
                "num_venues": self.num_venues,
                "num_edges": 0
            }
        
        # Convert to edge_index tensor [2, num_edges]
        edge_index = torch.tensor(all_edges, dtype=torch.long).t().contiguous()
        
        metadata = {
            "num_users": self.num_users,
            "num_venues": self.num_venues,
            "num_edges": edge_index.shape[1],
            "num_user_venue_edges": len(user_venue_edges),
            "num_user_user_edges": len(user_user_edges),
            "id_mappings": {
                "user_id_to_idx": self.user_id_to_idx,
                "venue_id_to_idx": self.venue_id_to_idx,
                "idx_to_user_id": self.idx_to_user_id,
                "idx_to_venue_id": self.idx_to_venue_id,
            }
        }
        
        logger.info(
            f"Built graph: {self.num_users} users, {self.num_venues} venues, "
            f"{edge_index.shape[1]} edges ({len(user_venue_edges)} user-venue, "
            f"{len(user_user_edges)} user-user)"
        )
        
        return edge_index, metadata

    async def _build_id_mappings(self, min_interactions: int):
        """Build mappings from DB IDs to graph indices."""
        # Get all users with at least min_interactions
        user_interaction_counts = select(
            UserInteraction.user_id,
            func.count(UserInteraction.id).label("count")
        ).group_by(UserInteraction.user_id).having(
            func.count(UserInteraction.id) >= min_interactions
        )
        
        user_result = await self.db.execute(user_interaction_counts)
        active_user_ids = [row[0] for row in user_result.all()]
        
        # Also get users with venue interests
        interest_user_query = select(VenueInterest.user_id).distinct()
        interest_result = await self.db.execute(interest_user_query)
        interest_user_ids = [row[0] for row in interest_result.all()]
        
        # Combine and deduplicate
        all_user_ids = sorted(set(active_user_ids + interest_user_ids))
        
        # Get all venues that have interactions
        venue_interaction_counts = select(
            UserInteraction.venue_id,
            func.count(UserInteraction.id).label("count")
        ).where(
            UserInteraction.venue_id.isnot(None)
        ).group_by(UserInteraction.venue_id).having(
            func.count(UserInteraction.id) >= min_interactions
        )
        
        venue_result = await self.db.execute(venue_interaction_counts)
        active_venue_ids = [row[0] for row in venue_result.all()]
        
        # Also get venues with interests
        interest_venue_query = select(VenueInterest.venue_id).distinct()
        interest_venue_result = await self.db.execute(interest_venue_query)
        interest_venue_ids = [row[0] for row in interest_venue_result.all()]
        
        # Combine and deduplicate
        all_venue_ids = sorted(set(active_venue_ids + interest_venue_ids))
        
        # Build mappings
        self.num_users = len(all_user_ids)
        self.num_venues = len(all_venue_ids)
        
        # User mappings: [0, num_users)
        for idx, user_id in enumerate(all_user_ids):
            self.user_id_to_idx[user_id] = idx
            self.idx_to_user_id[idx] = user_id
        
        # Venue mappings: [num_users, num_users + num_venues)
        for idx, venue_id in enumerate(all_venue_ids):
            graph_idx = self.num_users + idx
            self.venue_id_to_idx[venue_id] = graph_idx
            self.idx_to_venue_id[graph_idx] = venue_id

    async def _build_user_venue_edges(self) -> List[Tuple[int, int]]:
        """
        Build User-Venue edges from interactions.
        
        Returns list of (user_idx, venue_idx) tuples.
        """
        edges = []
        
        # Weight mapping for different interaction types
        interaction_weights = {
            InteractionType.VIEW: 1.0,
            InteractionType.SAVE: 3.0,
            InteractionType.SHARE: 2.0,
            InteractionType.LIKE: 2.5,
            InteractionType.REVIEW: 4.0,
        }
        
        # Get all user-venue interactions
        interactions_query = select(
            UserInteraction.user_id,
            UserInteraction.venue_id,
            UserInteraction.interaction_type,
            UserInteraction.duration_seconds
        ).where(
            and_(
                UserInteraction.venue_id.isnot(None),
                UserInteraction.user_id.in_(list(self.user_id_to_idx.keys())),
                UserInteraction.venue_id.in_(list(self.venue_id_to_idx.keys()))
            )
        )
        
        interactions_result = await self.db.execute(interactions_query)
        
        # Track edge weights (for multiple interactions, sum weights)
        edge_weights: Dict[Tuple[int, int], float] = {}
        
        for row in interactions_result.all():
            user_id, venue_id, interaction_type, duration = row
            
            if user_id not in self.user_id_to_idx or venue_id not in self.venue_id_to_idx:
                continue
            
            user_idx = self.user_id_to_idx[user_id]
            venue_idx = self.venue_id_to_idx[venue_id]
            
            # Base weight from interaction type
            weight = interaction_weights.get(interaction_type, 1.0)
            
            # Boost weight for longer views
            if interaction_type == InteractionType.VIEW and duration:
                weight += min(duration / 60.0, 2.0)  # Cap at +2.0
            
            edge_key = (user_idx, venue_idx)
            edge_weights[edge_key] = edge_weights.get(edge_key, 0.0) + weight
        
        # Get venue interests (explicit interest is strong signal)
        interests_query = select(
            VenueInterest.user_id,
            VenueInterest.venue_id,
            VenueInterest.interest_score,
            VenueInterest.explicitly_interested
        ).where(
            and_(
                VenueInterest.user_id.in_(list(self.user_id_to_idx.keys())),
                VenueInterest.venue_id.in_(list(self.venue_id_to_idx.keys()))
            )
        )
        
        interests_result = await self.db.execute(interests_query)
        
        for row in interests_result.all():
            user_id, venue_id, interest_score, explicitly_interested = row
            
            if user_id not in self.user_id_to_idx or venue_id not in self.venue_id_to_idx:
                continue
            
            user_idx = self.user_id_to_idx[user_id]
            venue_idx = self.venue_id_to_idx[venue_id]
            
            # Explicit interest gets high weight
            if explicitly_interested:
                weight = 5.0
            else:
                weight = interest_score * 3.0
            
            edge_key = (user_idx, venue_idx)
            edge_weights[edge_key] = edge_weights.get(edge_key, 0.0) + weight
        
        # Get bookings (strongest signal)
        bookings_query = select(
            Booking.user_id,
            Booking.venue_id
        ).where(
            and_(
                Booking.user_id.in_(list(self.user_id_to_idx.keys())),
                Booking.venue_id.in_(list(self.venue_id_to_idx.keys()))
            )
        )
        
        bookings_result = await self.db.execute(bookings_query)
        
        for row in bookings_result.all():
            user_id, venue_id = row
            
            if user_id not in self.user_id_to_idx or venue_id not in self.venue_id_to_idx:
                continue
            
            user_idx = self.user_id_to_idx[user_id]
            venue_idx = self.venue_id_to_idx[venue_id]
            
            # Booking is strongest signal
            edge_key = (user_idx, venue_idx)
            edge_weights[edge_key] = edge_weights.get(edge_key, 0.0) + 10.0
        
        # Convert weighted edges to list (we'll use multiple edges for high weights)
        # For simplicity, create one edge per interaction, but we could sample
        # based on weight if needed
        for (user_idx, venue_idx), weight in edge_weights.items():
            # Create multiple edges based on weight (rounded)
            num_edges = max(1, int(weight))
            for _ in range(min(num_edges, 10)):  # Cap at 10 edges per pair
                edges.append((user_idx, venue_idx))
        
        return edges

    async def _build_user_user_edges(self) -> List[Tuple[int, int]]:
        """
        Build User-User edges from friendships.
        
        Returns list of (user_idx1, user_idx2) tuples (bidirectional).
        """
        edges = []
        
        # Get all friendships where both users are in our graph
        friendships_query = select(
            Friendship.user_id,
            Friendship.friend_id
        ).where(
            and_(
                Friendship.user_id.in_(list(self.user_id_to_idx.keys())),
                Friendship.friend_id.in_(list(self.user_id_to_idx.keys()))
            )
        )
        
        friendships_result = await self.db.execute(friendships_query)
        
        for row in friendships_result.all():
            user_id, friend_id = row
            
            if user_id not in self.user_id_to_idx or friend_id not in self.user_id_to_idx:
                continue
            
            user_idx = self.user_id_to_idx[user_id]
            friend_idx = self.user_id_to_idx[friend_id]
            
            # Add bidirectional edges (undirected graph)
            edges.append((user_idx, friend_idx))
            edges.append((friend_idx, user_idx))  # Reverse edge
        
        return edges

    def get_user_idx(self, user_id: int) -> Optional[int]:
        """Get graph index for a user ID."""
        return self.user_id_to_idx.get(user_id)

    def get_venue_idx(self, venue_id: int) -> Optional[int]:
        """Get graph index for a venue ID."""
        return self.venue_id_to_idx.get(venue_id)

    def get_user_id(self, user_idx: int) -> Optional[int]:
        """Get database user ID from graph index."""
        return self.idx_to_user_id.get(user_idx)

    def get_venue_id(self, venue_idx: int) -> Optional[int]:
        """Get database venue ID from graph index."""
        return self.idx_to_venue_id.get(venue_idx)

