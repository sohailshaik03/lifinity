"""Pagination utilities for large datasets."""
from typing import Any, Dict, List, Tuple
import streamlit as st


def paginate_list(items: List[Any], page_size: int = 50) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Paginate a list of items with Streamlit controls.
    
    Args:
        items: List of items to paginate
        page_size: Number of items per page
        
    Returns:
        Tuple of (current_page_items, pagination_info)
    """
    total_items = len(items)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    
    # Initialize page number in session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    # Ensure current page is within bounds
    if st.session_state.current_page > total_pages:
        st.session_state.current_page = total_pages
    if st.session_state.current_page < 1:
        st.session_state.current_page = 1
    
    # Calculate start and end indices
    start_idx = (st.session_state.current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)
    
    # Get current page items
    current_items = items[start_idx:end_idx]
    
    pagination_info = {
        'current_page': st.session_state.current_page,
        'total_pages': total_pages,
        'total_items': total_items,
        'start_idx': start_idx + 1,  # 1-based for display
        'end_idx': end_idx,
        'page_size': page_size
    }
    
    return current_items, pagination_info


def render_pagination_controls(pagination_info: Dict[str, Any], key_prefix: str = ""):
    """
    Render pagination controls (Previous/Next buttons and page info).
    
    Args:
        pagination_info: Dictionary with pagination metadata
        key_prefix: Unique prefix for widget keys to avoid conflicts
    """
    total_pages = pagination_info['total_pages']
    current_page = pagination_info['current_page']
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if st.button("◀ Previous", disabled=(current_page <= 1), key=f"{key_prefix}_prev"):
            st.session_state.current_page -= 1
            st.rerun()
    
    with col2:
        st.markdown(
            f"<div style='text-align: center; padding: 8px;'>"
            f"Page {current_page} of {total_pages} "
            f"({pagination_info['start_idx']}-{pagination_info['end_idx']} "
            f"of {pagination_info['total_items']} items)"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col3:
        if st.button("Next ▶", disabled=(current_page >= total_pages), key=f"{key_prefix}_next"):
            st.session_state.current_page += 1
            st.rerun()


def reset_pagination(page_num: int = 1):
    """Reset pagination to a specific page (default: 1)."""
    st.session_state.current_page = page_num


def get_db_pagination_params(page: int = 1, page_size: int = 50) -> Tuple[int, int]:
    """
    Calculate LIMIT and OFFSET for database queries.
    
    Args:
        page: Current page number (1-based)
        page_size: Number of items per page
        
    Returns:
        Tuple of (limit, offset)
    """
    offset = (page - 1) * page_size
    return page_size, offset
