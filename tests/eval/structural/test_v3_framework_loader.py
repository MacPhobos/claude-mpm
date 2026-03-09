"""V3 Verification Test: FrameworkLoader works in pytest context.

This test verifies that FrameworkLoader can be instantiated with
validate_api_keys=False and produces valid PM instructions content.

Part of Phase 0 pre-implementation verification (V3).
This test will also serve as the foundation for Tier 1 structural tests.
"""

import pytest


@pytest.mark.eval
@pytest.mark.structural
class TestFrameworkLoaderV3:
    """Verify FrameworkLoader works in pytest context (V3)."""

    def test_framework_loader_instantiates(self):
        """FrameworkLoader can be created with validate_api_keys=False."""
        from claude_mpm.core.framework_loader import FrameworkLoader

        loader = FrameworkLoader(config={"validate_api_keys": False})
        assert loader is not None

    def test_framework_loader_returns_string(self):
        """get_framework_instructions() returns a non-empty string."""
        from claude_mpm.core.framework_loader import FrameworkLoader

        loader = FrameworkLoader(config={"validate_api_keys": False})
        content = loader.get_framework_instructions()

        assert isinstance(content, str), f"Expected str, got {type(content)}"
        assert len(content) > 0, "Instructions content is empty"

    def test_framework_loader_content_size(self):
        """Loaded content is substantial (>1000 bytes for real PM prompt)."""
        from claude_mpm.core.framework_loader import FrameworkLoader

        loader = FrameworkLoader(config={"validate_api_keys": False})
        content = loader.get_framework_instructions()

        # PM instructions are typically 50KB+
        assert len(content) > 1000, (
            f"Content too small ({len(content)} bytes), "
            "expected PM instructions >1000 bytes"
        )

    def test_framework_loader_contains_pm_content(self):
        """Content contains PM-specific instruction markers."""
        from claude_mpm.core.framework_loader import FrameworkLoader

        loader = FrameworkLoader(config={"validate_api_keys": False})
        content = loader.get_framework_instructions()

        # Check for key PM instruction markers
        pm_markers = [
            "PM",  # Basic PM reference
            "delegat",  # delegation/delegate
            "agent",  # agent references
        ]

        found_markers = [m for m in pm_markers if m.lower() in content.lower()]
        assert len(found_markers) >= 2, (
            f"Expected at least 2 PM markers, found {len(found_markers)}: {found_markers}. "
            "Content may not be PM instructions."
        )

    def test_framework_loader_idempotent(self):
        """Multiple calls return consistent content (V12 prerequisite)."""
        from claude_mpm.core.framework_loader import FrameworkLoader

        loader = FrameworkLoader(config={"validate_api_keys": False})
        content1 = loader.get_framework_instructions()
        content2 = loader.get_framework_instructions()

        assert content1 == content2, (
            f"Content differs between calls: {len(content1)} vs {len(content2)} bytes"
        )
