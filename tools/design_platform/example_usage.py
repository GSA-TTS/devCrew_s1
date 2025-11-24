"""
Example usage of FigmaClient for the design_platform tool.

This file demonstrates all major features of the FigmaClient implementation.
"""

from figma_client import FigmaClient


def example_basic_usage():
    """Example 1: Basic file retrieval."""
    # Initialize client with access token
    figma = FigmaClient(access_token="figd_xxx")

    # Get file structure and properties
    file = figma.get_file(file_key="ABC123")
    print(f"File name: {file.name}")
    print(f"Last modified: {file.last_modified}")
    print(f"Version: {file.version}")
    print(f"Root node type: {file.document.type}")


def example_export_nodes():
    """Example 2: Export nodes as images."""
    figma = FigmaClient(access_token="figd_xxx")

    # Export multiple nodes as PNG at 2x scale
    exports = figma.export_nodes(
        file_key="ABC123",
        node_ids=["1:5", "1:6", "1:7"],
        export_format="png",
        scale=2.0,
        download=True,
    )

    # Process exports
    for export in exports:
        if export.error:
            print(f"Export failed for {export.node_id}: {export.error}")
        else:
            print(f"Exported {export.node_id}: {export.url}")
            if export.image_data:
                # Save image to disk
                with open(f"{export.node_id.replace(':', '_')}.png", "wb") as f:
                    f.write(export.image_data)


def example_get_components():
    """Example 3: Extract all components from a file."""
    figma = FigmaClient(access_token="figd_xxx")

    # Get all component definitions
    components = figma.get_components(file_key="ABC123")

    print(f"Found {len(components)} components:")
    for component in components:
        print(f"  - {component.name} (ID: {component.id})")
        if component.absolute_bounding_box:
            bbox = component.absolute_bounding_box
            print(f"    Size: {bbox.width}x{bbox.height}")


def example_get_styles():
    """Example 4: Retrieve design styles."""
    figma = FigmaClient(access_token="figd_xxx")

    # Get design styles organized by type
    styles = figma.get_styles(file_key="ABC123")

    print(f"Fill styles: {len(styles['fill'])}")
    print(f"Text styles: {len(styles['text'])}")
    print(f"Effect styles: {len(styles['effect'])}")
    print(f"Grid styles: {len(styles['grid'])}")


def example_post_comment():
    """Example 5: Post a comment on a design."""
    figma = FigmaClient(access_token="figd_xxx")

    # Post comment at specific coordinates
    comment = figma.post_comment(
        file_key="ABC123",
        message="This button needs to be larger for accessibility",
        position={"x": 100.5, "y": 200.3},
    )

    print(f"Comment posted successfully: {comment.get('id')}")


def example_error_handling():
    """Example 6: Error handling patterns."""
    from figma_client import (
        AuthenticationError,
        NotFoundError,
        RateLimitError,
        FigmaAPIError,
    )

    figma = FigmaClient(access_token="figd_xxx")

    try:
        figma_file = figma.get_file(file_key="INVALID_KEY")
        print(f"Retrieved file: {figma_file.name}")
    except NotFoundError as e:
        print(f"File not found: {e.message}")
    except AuthenticationError:
        print("Invalid access token")
    except RateLimitError as e:
        print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
    except FigmaAPIError as e:
        print(f"API error: {e.message} (status: {e.status_code})")


def example_context_manager():
    """Example 7: Using context manager for automatic cleanup."""
    # Client automatically closes session when exiting context
    with FigmaClient(access_token="figd_xxx") as figma:
        figma_file = figma.get_file(file_key="ABC123")
        print(f"Processing file: {figma_file.name}")
        # Session automatically closed after this block


def example_advanced_export():
    """Example 8: Advanced export with SVG and PDF formats."""
    figma = FigmaClient(access_token="figd_xxx")

    # Export as SVG (vector format)
    svg_exports = figma.export_nodes(
        file_key="ABC123", node_ids=["1:5"], export_format="svg", download=False
    )
    print(f"Exported {len(svg_exports)} SVG files")

    # Export as PDF with custom scale
    pdf_exports = figma.export_nodes(
        file_key="ABC123",
        node_ids=["1:6"],
        export_format="pdf",
        scale=1.5,
        download=True,
    )
    print(f"Exported {len(pdf_exports)} PDF files")


def example_get_specific_nodes():
    """Example 9: Get specific nodes by ID."""
    figma = FigmaClient(access_token="figd_xxx")

    # Get specific nodes
    nodes = figma.get_file_nodes(file_key="ABC123", node_ids=["1:5", "1:6", "1:7"])

    for node_id, node in nodes.items():
        print(f"Node {node_id}:")
        print(f"  Name: {node.name}")
        print(f"  Type: {node.type}")
        if node.background_color:
            print(f"  Background: {node.background_color.to_hex()}")


def example_version_history():
    """Example 10: Get file version history."""
    figma = FigmaClient(access_token="figd_xxx")

    # Get recent versions
    versions = figma.get_file_versions(file_key="ABC123", page_size=10)

    print(f"Recent versions ({len(versions)}):")
    for version in versions:
        print(f"  - {version.get('label', 'Unnamed')}: {version.get('created_at')}")


if __name__ == "__main__":
    print("Figma API Client - Example Usage")
    print("=" * 50)
    print("\nNote: Replace 'figd_xxx' with your actual Figma access token")
    print("and 'ABC123' with your actual file key.\n")

    # Uncomment examples to run them
    # example_basic_usage()
    # example_export_nodes()
    # example_get_components()
    # example_get_styles()
    # example_post_comment()
    # example_error_handling()
    # example_context_manager()
    # example_advanced_export()
    # example_get_specific_nodes()
    # example_version_history()
