"""
Metric Cards and Small Widget Components.
"""
import streamlit as st

def render_metric_card(title: str, value: str, delta: str = None, color: str = "normal"):
    """
    Renders a standard metric card.
    Uses basic Streamlit st.metric by default. Custom styling can be applied here.
    """
    st.metric(label=title, value=value, delta=delta, delta_color=color)

def render_spending_limit_widget():
    """Renders the Zahlungslimit progress bar widget."""
    pass

def render_creditor_overview_widget():
    """Renders the Top 5 creditors widget."""
    pass
