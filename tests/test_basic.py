"""Basic tests to ensure imports work."""

def test_import_orchestrator():
    """Test that orchestrator can be imported."""
    from lithic_cli.orchestrator import Orchestrator
    assert Orchestrator is not None

def test_import_config():
    """Test that config can be imported.""" 
    from lithic_cli.config import AgentConfig
    assert AgentConfig is not None

def test_import_plugins():
    """Test that plugins can be imported."""
    from lithic_cli.plugins.manager import get_plugin_manager
    assert get_plugin_manager is not None

def test_import_caching():
    """Test that caching can be imported."""
    from lithic_cli.caching import get_cache
    assert get_cache is not None