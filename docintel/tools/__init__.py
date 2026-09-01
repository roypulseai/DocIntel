"""Cross-platform helper to stop a running DocIntel/Streamlit server.

The canonical implementation lives in ``docintel.tools.stop_server``; this
package exposes it as ``docintel.tools.stop_streamlit`` for convenience.
"""
from docintel.tools.stop_server import (
    PORT,
    _find_pids_by_port,
    stop_streamlit,
)

__all__ = ["PORT", "stop_streamlit", "_find_pids_by_port"]
