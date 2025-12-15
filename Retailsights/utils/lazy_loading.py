"""Lazy loading wrapper for dashboard components."""
import streamlit as st
from typing import Callable, Any


def lazy_component(title: str, render_func: Callable[..., None], *args, **kwargs):
    """
    Render a component with lazy loading - only loads when expanded.
    
    Args:
        title: Component title for the expander
        render_func: Function to call to render the component
        *args, **kwargs: Arguments to pass to render_func
    """
    with st.expander(title, expanded=False):
        render_func(*args, **kwargs)


def tabs_with_lazy_loading(tab_names: list, render_funcs: list, *args_list):
    """
    Create tabs where content only renders when the tab is selected.
    
    Args:
        tab_names: List of tab names
        render_funcs: List of functions to render each tab
        args_list: List of tuples containing arguments for each render function
    """
    tabs = st.tabs(tab_names)
    
    # Initialize active tab in session state
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 0
    
    for i, tab in enumerate(tabs):
        with tab:
            # Only render the currently selected tab
            if i == st.session_state.active_tab or st.session_state.get(f'tab_{i}_loaded', False):
                if args_list and i < len(args_list):
                    render_funcs[i](*args_list[i])
                else:
                    render_funcs[i]()
                st.session_state[f'tab_{i}_loaded'] = True


@st.cache_data(ttl=300, show_spinner="Loading chart...")
def cached_chart_data(query_func: Callable, *args, **kwargs) -> Any:
    """Cache expensive chart data computations."""
    return query_func(*args, **kwargs)
