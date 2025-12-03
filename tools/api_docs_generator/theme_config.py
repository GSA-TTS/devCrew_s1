"""
Theme Configuration

Provides theme management and color schemes for API documentation renderers.
Supports light and dark themes with customizable color palettes.

Classes:
    ThemeConfig: Theme configuration manager

Example:
    >>> from theme_config import ThemeConfig
    >>> config = ThemeConfig()
    >>> colors = config.get_swagger_theme("dark")
    >>> print(colors["primary"])
    '#5ca3ff'
"""

from typing import Dict


class ThemeConfig:
    """
    Theme configuration manager for documentation renderers.

    Provides predefined color schemes for light and dark themes,
    including colors for UI elements, HTTP methods, and syntax
    highlighting.

    Attributes:
        _themes: Dictionary of theme configurations
    """

    def __init__(self) -> None:
        """Initialize theme configuration with default color schemes."""
        self._themes = {
            "light": {
                "background": "#ffffff",
                "text": "#333333",
                "secondary": "#666666",
                "primary": "#4990e2",
                "primary_dark": "#357abd",
                "border": "#e0e0e0",
                "card_bg": "#ffffff",
                "hover_bg": "#f5f5f5",
                "topbar_bg": "#f8f9fa",
                "table_header_bg": "#fafafa",
                "code_bg": "#f5f5f5",
                "success": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "method_get": "#61affe",
                "method_post": "#49cc90",
                "method_put": "#fca130",
                "method_delete": "#f93e3e",
                "method_patch": "#50e3c2",
            },
            "dark": {
                "background": "#1a1a1a",
                "text": "#e0e0e0",
                "secondary": "#a0a0a0",
                "primary": "#5ca3ff",
                "primary_dark": "#4990e2",
                "border": "#333333",
                "card_bg": "#242424",
                "hover_bg": "#2d2d2d",
                "topbar_bg": "#1f1f1f",
                "table_header_bg": "#2a2a2a",
                "code_bg": "#2d2d2d",
                "success": "#28a745",
                "warning": "#ffc107",
                "error": "#dc3545",
                "method_get": "#61affe",
                "method_post": "#49cc90",
                "method_put": "#fca130",
                "method_delete": "#f93e3e",
                "method_patch": "#50e3c2",
            },
        }

    def get_swagger_theme(self, theme: str = "light") -> Dict[str, str]:
        """
        Get Swagger UI theme colors.

        Args:
            theme: Theme name ("light" or "dark")

        Returns:
            Dictionary of color values

        Raises:
            ValueError: If theme name is invalid

        Example:
            >>> config = ThemeConfig()
            >>> colors = config.get_swagger_theme("light")
            >>> colors["primary"]
            '#4990e2'
        """
        if theme not in self._themes:
            raise ValueError(
                f"Invalid theme: {theme}. "
                f"Available themes: {list(self._themes.keys())}"
            )
        return self._themes[theme].copy()

    def get_redoc_theme(self, theme: str = "light") -> Dict[str, str]:
        """
        Get Redoc theme colors.

        Extends base theme with Redoc-specific color keys for sidebar,
        panel, and other Redoc UI elements.

        Args:
            theme: Theme name ("light" or "dark")

        Returns:
            Dictionary of color values including Redoc-specific keys

        Raises:
            ValueError: If theme name is invalid

        Example:
            >>> config = ThemeConfig()
            >>> colors = config.get_redoc_theme("dark")
            >>> colors["sidebar_bg"]
            '#2a2a2a'
        """
        base_colors = self.get_swagger_theme(theme)

        # Add Redoc-specific colors
        redoc_colors = base_colors.copy()
        redoc_colors.update(
            {
                "sidebar_bg": ("#fafafa" if theme == "light" else "#2a2a2a"),
                "sidebar_text": ("#333333" if theme == "light" else "#e0e0e0"),
                "panel_bg": "#263238" if theme == "dark" else "#f7f7f7",
            }
        )

        return redoc_colors

    def add_custom_theme(
        self,
        name: str,
        colors: Dict[str, str],
    ) -> None:
        """
        Add a custom theme configuration.

        Validates that required color keys are present before adding
        the theme. Partial themes are not allowed.

        Args:
            name: Theme name (will be available via get_*_theme methods)
            colors: Dictionary of color values with required keys

        Raises:
            ValueError: If required color keys are missing

        Example:
            >>> config = ThemeConfig()
            >>> custom = {
            ...     "background": "#fafafa",
            ...     "text": "#222222",
            ...     "secondary": "#555555",
            ...     "primary": "#3498db",
            ...     "border": "#dddddd",
            ...     "card_bg": "#ffffff",
            ... }
            >>> config.add_custom_theme("custom", custom)
        """
        required_keys = {
            "background",
            "text",
            "secondary",
            "primary",
            "border",
            "card_bg",
        }

        missing_keys = required_keys - set(colors.keys())
        if missing_keys:
            raise ValueError(f"Missing required color keys: {missing_keys}")

        self._themes[name] = colors

    def list_themes(self) -> list:
        """
        List available theme names.

        Returns:
            List of theme names as strings

        Example:
            >>> config = ThemeConfig()
            >>> config.list_themes()
            ['light', 'dark']
        """
        return list(self._themes.keys())

    def get_theme_colors(self, theme: str = "light") -> Dict[str, str]:
        """
        Get raw theme colors without modifications.

        This is a lower-level method that returns the exact color
        dictionary stored for a theme, without any Redoc-specific
        or renderer-specific additions.

        Args:
            theme: Theme name

        Returns:
            Dictionary of color values

        Raises:
            ValueError: If theme name is invalid

        Example:
            >>> config = ThemeConfig()
            >>> colors = config.get_theme_colors("light")
            >>> "primary" in colors
            True
        """
        if theme not in self._themes:
            raise ValueError(
                f"Invalid theme: {theme}. "
                f"Available themes: {list(self._themes.keys())}"
            )
        return self._themes[theme].copy()

    def update_theme_colors(
        self,
        theme: str,
        updates: Dict[str, str],
    ) -> None:
        """
        Update specific colors in an existing theme.

        Allows partial updates to theme colors without replacing
        the entire theme configuration.

        Args:
            theme: Theme name to update
            updates: Dictionary of color keys to update

        Raises:
            ValueError: If theme doesn't exist

        Example:
            >>> config = ThemeConfig()
            >>> config.update_theme_colors("light", {
            ...     "primary": "#0066cc",
            ...     "primary_dark": "#004999"
            ... })
        """
        if theme not in self._themes:
            raise ValueError(
                f"Theme not found: {theme}. "
                f"Available themes: {list(self._themes.keys())}"
            )

        self._themes[theme].update(updates)

    def export_theme(self, theme: str) -> Dict[str, str]:
        """
        Export a theme configuration for serialization.

        Returns a copy of the theme colors that can be safely
        modified or serialized without affecting the internal state.

        Args:
            theme: Theme name to export

        Returns:
            Dictionary of color values (deep copy)

        Raises:
            ValueError: If theme doesn't exist

        Example:
            >>> config = ThemeConfig()
            >>> exported = config.export_theme("dark")
            >>> import json
            >>> json.dumps(exported)
            '{"background": "#1a1a1a", ...}'
        """
        if theme not in self._themes:
            raise ValueError(
                f"Theme not found: {theme}. "
                f"Available themes: {list(self._themes.keys())}"
            )
        return self._themes[theme].copy()

    def import_theme(
        self,
        name: str,
        colors: Dict[str, str],
        validate: bool = True,
    ) -> None:
        """
        Import a theme configuration from external source.

        Args:
            name: Theme name
            colors: Dictionary of color values
            validate: Whether to validate required keys

        Raises:
            ValueError: If validation fails

        Example:
            >>> config = ThemeConfig()
            >>> theme_data = {...}  # Load from JSON/YAML
            >>> config.import_theme("imported", theme_data)
        """
        if validate:
            self.add_custom_theme(name, colors)
        else:
            self._themes[name] = colors.copy()

    def remove_theme(self, theme: str) -> None:
        """
        Remove a custom theme.

        Cannot remove built-in themes (light, dark).

        Args:
            theme: Theme name to remove

        Raises:
            ValueError: If trying to remove built-in theme or
                       theme doesn't exist

        Example:
            >>> config = ThemeConfig()
            >>> config.add_custom_theme("temp", {...})
            >>> config.remove_theme("temp")
        """
        if theme in ["light", "dark"]:
            raise ValueError(f"Cannot remove built-in theme: {theme}")

        if theme not in self._themes:
            raise ValueError(f"Theme not found: {theme}")

        del self._themes[theme]
