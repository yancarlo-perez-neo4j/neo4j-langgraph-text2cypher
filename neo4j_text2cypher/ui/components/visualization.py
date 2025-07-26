"""Neo4j graph visualization component for Streamlit."""

from typing import Optional
import streamlit as st
import streamlit.components.v1 as components
from neo4j_viz.neo4j import from_neo4j
from neo4j import Result


def render_neo4j_graph_from_result(
    result: Result,
    height: int = 600,
    node_color_property: str = "labels",
    node_size_property: Optional[str] = None
) -> None:
    """
    Render Neo4j Result.graph as an interactive visualization.
    
    Parameters
    ----------
    result : neo4j.Result
        The Neo4j Result object with graph transformer applied
    height : int, optional
        Height of the visualization in pixels, by default 600
    node_color_property : str, optional
        Property to use for node coloring, by default "labels"
    node_size_property : Optional[str], optional
        Property to use for node sizing, by default None
    """
    try:
        # Create visualization directly from Neo4j result
        viz = from_neo4j(result)
        
        # Apply styling
        if node_color_property:
            viz.color_nodes(property=node_color_property)
        
        if node_size_property:
            viz.resize_nodes(property=node_size_property)
        
        # Render the visualization
        html_content = viz.render()._repr_html_()
        
        # Display in Streamlit
        components.html(html_content, height=height, scrolling=True)
        
        # Show statistics
        if hasattr(result, 'nodes') and hasattr(result, 'relationships'):
            st.caption(f"Graph contains {len(result.nodes)} nodes and {len(result.relationships)} relationships")
        
    except Exception as e:
        st.error(f"Error rendering graph visualization: {str(e)}")
        st.exception(e)