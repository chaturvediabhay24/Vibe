"""
User matching module for chat application.
This module handles the logic for pairing users in the chat application.
It can be extended or replaced with custom matching logic in the future.
"""

import asyncio
import logging
from typing import Dict, Optional, List, Tuple
import uuid

logger = logging.getLogger(__name__)

class ChatMatcher:
    """
    A class that handles matching users for chat sessions.
    """
    def __init__(self):
        # Dictionary to store waiting users: {user_id: waiting_future}
        self.waiting_users: Dict[str, asyncio.Future] = {}
        # Dictionary to store active chat pairs: {user_id: partner_id}
        self.active_pairs: Dict[str, str] = {}
        # Lock to prevent race conditions
        self.lock = asyncio.Lock()
    
    async def find_match(self, user_id: str) -> str:
        """
        Find a match for the given user.
        If no users are waiting, the user will be added to the waiting list.
        If a user is waiting, they will be matched together.
        
        Args:
            user_id: The ID of the user looking for a match
            
        Returns:
            The ID of the matched partner, or None if the user is waiting
        """
        # First check if this user is already in an active pair (without lock)
        if user_id in self.active_pairs:
            return self.active_pairs[user_id]
        
        async with self.lock:
            # Check again with the lock (in case it changed while waiting for lock)
            if user_id in self.active_pairs:
                return self.active_pairs[user_id]
            
            # Check if this user is already waiting (shouldn't happen, but just in case)
            if user_id in self.waiting_users:
                # User is already waiting, just return their future
                return await self.waiting_users[user_id]
            
            # If there are waiting users, match with one of them
            if self.waiting_users:
                # Get all waiting users
                waiting_users = list(self.waiting_users.keys())
                
                # Find a waiting user that isn't this user
                waiting_user_id = None
                for wuid in waiting_users:
                    if wuid != user_id:
                        waiting_user_id = wuid
                        break
                
                # If we found a waiting user to match with
                if waiting_user_id:
                    # Get the future for the waiting user
                    waiting_future = self.waiting_users.pop(waiting_user_id)
                    
                    # Create a pair
                    self.active_pairs[user_id] = waiting_user_id
                    self.active_pairs[waiting_user_id] = user_id
                    
                    logger.info(f"Matched users: {user_id} and {waiting_user_id}")
                    
                    # Resolve the waiting future with the new user's ID
                    if not waiting_future.done():
                        waiting_future.set_result(user_id)
                    
                    return waiting_user_id
            
            # No suitable waiting users, so this user will wait
            future = asyncio.Future()
            self.waiting_users[user_id] = future
            
            logger.info(f"User {user_id} is waiting for a match (no other users or only self)")
            
            # Start a background task to periodically check for other waiting users
            # This helps in case two users connect at almost the same time
            asyncio.create_task(self._check_for_matches(user_id))
            
            try:
                # Wait for someone to match with this user
                partner_id = await future
                return partner_id
            except asyncio.CancelledError:
                # If the future is cancelled (e.g., user disconnects), remove from waiting list
                if user_id in self.waiting_users:
                    del self.waiting_users[user_id]
                raise
    
    async def _check_for_matches(self, user_id: str) -> None:
        """
        Periodically check if there are other waiting users that this user can match with.
        This helps resolve race conditions where two users connect at almost the same time.
        
        Args:
            user_id: The ID of the user to check matches for
        """
        # Wait a short time to allow other connections to be processed
        await asyncio.sleep(0.5)
        
        # Only proceed if the user is still waiting
        if user_id not in self.waiting_users:
            return
        
        async with self.lock:
            # Check again with the lock
            if user_id not in self.waiting_users or user_id in self.active_pairs:
                return
            
            # Get all waiting users except this one
            waiting_users = [uid for uid in self.waiting_users.keys() if uid != user_id]
            
            if waiting_users:
                # Match with the first waiting user
                waiting_user_id = waiting_users[0]
                
                # Get the futures for both users
                user_future = self.waiting_users.pop(user_id)
                waiting_future = self.waiting_users.pop(waiting_user_id)
                
                # Create a pair
                self.active_pairs[user_id] = waiting_user_id
                self.active_pairs[waiting_user_id] = user_id
                
                logger.info(f"Matched users (from background check): {user_id} and {waiting_user_id}")
                
                # Resolve both futures
                if not user_future.done():
                    user_future.set_result(waiting_user_id)
                if not waiting_future.done():
                    waiting_future.set_result(user_id)
    
    def cancel_waiting(self, user_id: str) -> None:
        """
        Cancel waiting for a match for the given user.
        
        Args:
            user_id: The ID of the user to cancel waiting for
        """
        if user_id in self.waiting_users:
            future = self.waiting_users.pop(user_id)
            if not future.done():
                future.cancel()
            logger.info(f"User {user_id} cancelled waiting for a match")
    
    def end_chat(self, user_id: str) -> Optional[str]:
        """
        End a chat session for the given user.
        
        Args:
            user_id: The ID of the user ending the chat
            
        Returns:
            The ID of the partner who was in the chat, or None if not in a chat
        """
        if user_id in self.active_pairs:
            partner_id = self.active_pairs.pop(user_id)
            if partner_id in self.active_pairs:
                self.active_pairs.pop(partner_id)
            logger.info(f"Ended chat between {user_id} and {partner_id}")
            return partner_id
        return None
    
    def get_waiting_count(self) -> int:
        """
        Get the number of users waiting for a match.
        
        Returns:
            The number of waiting users
        """
        return len(self.waiting_users)
    
    def get_active_pairs_count(self) -> int:
        """
        Get the number of active chat pairs.
        
        Returns:
            The number of active chat pairs
        """
        return len(self.active_pairs) // 2  # Divide by 2 because each pair is counted twice

# Create a singleton instance
matcher = ChatMatcher()
