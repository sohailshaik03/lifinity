"""
Persistent Session Manager using browser cookies
Allows "Remember Me" functionality across browser sessions
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import streamlit as st

try:
    import extra_streamlit_components as stx
    COOKIES_AVAILABLE = True
except ImportError:
    COOKIES_AVAILABLE = False


class SessionManager:
    """Manages persistent user sessions with secure tokens"""
    
    # Cookie expiry: 30 days
    COOKIE_EXPIRY_DAYS = 30
    
    def __init__(self):
        """Initialize cookie manager"""
        if COOKIES_AVAILABLE:
            self.cookie_manager = stx.CookieManager(key="session_cookie_manager")
        else:
            self.cookie_manager = None
    
    @staticmethod
    def generate_session_token(user_id: int) -> str:
        """Generate a secure session token"""
        random_part = secrets.token_hex(16)
        timestamp = str(datetime.now().timestamp())
        combined = f"{user_id}:{timestamp}:{random_part}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def save_session(self, user: Dict[str, Any], remember_me: bool = False):
        """Save user session to cookies and session state"""
        try:
            user_id = user.get("id")
            if not user_id:
                return
            
            # Always save to session state as primary storage
            st.session_state["_persistent_user_id"] = str(user_id)
            st.session_state["_persistent_user_email"] = user.get("email", "")
            st.session_state["_persistent_user_name"] = user.get("full_name", "")
            st.session_state["_persistent_user_role"] = user.get("role", "")
            
            # Also try cookies if available
            if not self.cookie_manager:
                return
            
            # Generate secure token
            token = self.generate_session_token(user_id)
            
            # Calculate expiry
            expiry_days = self.COOKIE_EXPIRY_DAYS if remember_me else 1
            expiry = datetime.now() + timedelta(days=expiry_days)
            
            # Save to cookies
            self.cookie_manager.set(
                "auth_token", 
                token,
                expires_at=expiry,
                key="auth_token_cookie"
            )
            self.cookie_manager.set(
                "user_id",
                str(user_id),
                expires_at=expiry,
                key="user_id_cookie"
            )
            self.cookie_manager.set(
                "user_email",
                user.get("email", ""),
                expires_at=expiry,
                key="user_email_cookie"
            )
            
        except Exception as e:
            # Silently fail - cookies are enhancement, not critical
            pass
    
    def load_session(self) -> Optional[Dict[str, Any]]:
        """Load user session from session state or cookies"""
        # First try session state (fastest and most reliable)
        user_id_str = st.session_state.get("_persistent_user_id")
        if user_id_str:
            try:
                from Retailsights.repositories.users_repo import get_user_by_id
                user = get_user_by_id(int(user_id_str))
                if user and user.get("is_active"):
                    return {
                        "id": user["id"],
                        "email": user["email"],
                        "full_name": user["full_name"],
                        "role": user["role"],
                    }
            except Exception:
                pass
        
        # Fallback to cookies if available
        if not self.cookie_manager:
            return None
        
        try:
            # Get cookies
            cookies = self.cookie_manager.get_all()
            
            if not cookies:
                return None
            
            user_id = cookies.get("user_id")
            auth_token = cookies.get("auth_token")
            
            if not user_id or not auth_token:
                return None
            
            # Fetch user from database
            from Retailsights.repositories.users_repo import get_user_by_id
            user = get_user_by_id(int(user_id))
            
            if not user:
                # User deleted or invalid
                self.clear_session()
                return None
            
            if not user.get("is_active"):
                # User deactivated
                self.clear_session()
                return None
            
            # Return safe user data
            return {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
            }
            
        except Exception as e:
            # Silently fail and clear corrupted cookies
            self.clear_session()
            return None
    
    def clear_session(self):
        """Clear all session data"""
        # Clear session state
        for key in ["_persistent_user_id", "_persistent_user_email", "_persistent_user_name", "_persistent_user_role"]:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear cookies if available
        if not self.cookie_manager:
            return
            
        try:
            self.cookie_manager.delete("auth_token")
            self.cookie_manager.delete("user_id")
            self.cookie_manager.delete("user_email")
        except Exception:
            pass
    
    def is_session_valid(self) -> bool:
        """Check if there's a valid session"""
        # Check session state first (faster)
        if st.session_state.get("_persistent_user_id"):
            return True
        
        # Check cookies
        if not self.cookie_manager:
            return False
            
        try:
            cookies = self.cookie_manager.get_all()
            return bool(cookies and cookies.get("user_id") and cookies.get("auth_token"))
        except Exception:
            return False
