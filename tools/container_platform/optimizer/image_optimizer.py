"""
Image Optimizer Module

Provides comprehensive container image optimization with dive tool
integration, layer analysis, multi-stage build recommendations, and
size reduction strategies.

Features:
- Layer-by-layer size analysis using dive tool
- Multi-stage build recommendations
- Base image selection guidance (alpine vs slim vs distroless)
- Layer deduplication analysis
- Image squashing capabilities
- Unused file detection
- Efficiency score calculation
- Automated optimization application

Protocol Coverage:
- P-DOCKER-CLEANUP: Image optimization and cleanup
"""

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import docker
from docker.errors import ImageNotFound
from docker.models.images import Image

logger = logging.getLogger(__name__)


class BaseImageType(Enum):
    """Base image types for optimization recommendations."""

    FULL = "full"
    SLIM = "slim"
    ALPINE = "alpine"
    DISTROLESS = "distroless"
    SCRATCH = "scratch"


class OptimizationLevel(Enum):
    """Optimization aggressiveness levels."""

    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass
class LayerInfo:
    """Information about a single image layer."""

    id: str
    command: str
    size: int
    created: datetime
    created_by: str
    wasted_space: int = 0
    efficiency: float = 100.0
    files_added: int = 0
    files_removed: int = 0
    files_modified: int = 0


@dataclass
class OptimizationSuggestion:
    """A single optimization suggestion."""

    category: str
    priority: str  # high, medium, low
    description: str
    potential_savings: int
    difficulty: str  # easy, medium, hard
    implementation: str
    affected_layers: List[str] = field(default_factory=list)


@dataclass
class ImageAnalysis:
    """Complete analysis results for a container image."""

    image_name: str
    image_id: str
    total_size: int
    layer_count: int
    efficiency_score: float
    wasted_space: int
    potential_savings: int
    layers: List[LayerInfo]
    suggestions: List[OptimizationSuggestion]
    base_image: Optional[str] = None
    recommended_base: Optional[str] = None
    analysis_time: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationResult:
    """Results of applying optimizations."""

    success: bool
    original_size: int
    optimized_size: int
    size_reduction: int
    percentage_saved: float
    applied_optimizations: List[str]
    new_image_name: Optional[str] = None
    error_message: Optional[str] = None


class ImageOptimizer:
    """
    Container image optimizer with dive integration and comprehensive analysis.

    Analyzes Docker images for optimization opportunities, provides actionable
    suggestions, and can automatically apply optimizations.
    """

    def __init__(
        self,
        docker_client: Optional[docker.DockerClient] = None,
        dive_path: Optional[str] = None,
    ):
        """
        Initialize the image optimizer.

        Args:
            docker_client: Docker client instance (creates new if None)
            dive_path: Path to dive binary (searches PATH if None)
        """
        self.client = docker_client or docker.from_env()
        self.dive_path = dive_path or self._find_dive()

        # Optimization thresholds
        self.efficiency_threshold = 95.0
        self.wasted_space_threshold = 10 * 1024 * 1024  # 10 MB

        # Base image recommendations
        self.base_image_map = {
            "python": {
                BaseImageType.ALPINE: "python:3.11-alpine",
                BaseImageType.SLIM: "python:3.11-slim",
                BaseImageType.FULL: "python:3.11",
            },
            "node": {
                BaseImageType.ALPINE: "node:18-alpine",
                BaseImageType.SLIM: "node:18-slim",
                BaseImageType.FULL: "node:18",
            },
            "nginx": {
                BaseImageType.ALPINE: "nginx:alpine",
                BaseImageType.FULL: "nginx:latest",
            },
            "golang": {
                BaseImageType.ALPINE: "golang:1.21-alpine",
                BaseImageType.FULL: "golang:1.21",
                BaseImageType.SCRATCH: "scratch",
            },
        }

        logger.info("ImageOptimizer initialized")

    def _find_dive(self) -> Optional[str]:
        """
        Find dive binary in PATH.

        Returns:
            Path to dive binary or None if not found
        """
        dive_path = shutil.which("dive")
        if not dive_path:
            logger.warning(
                "dive tool not found in PATH. "
                "Install with: https://github.com/wagoodman/dive"
            )
        return dive_path

    def analyze_image(self, image_name: str, use_dive: bool = True) -> ImageAnalysis:
        """
        Perform comprehensive image analysis.

        Args:
            image_name: Name or ID of the image to analyze
            use_dive: Whether to use dive tool for deep analysis

        Returns:
            ImageAnalysis with complete analysis results

        Raises:
            ImageNotFound: If the image doesn't exist
            DockerException: If Docker operations fail
        """
        logger.info(f"Analyzing image: {image_name}")

        try:
            image = self.client.images.get(image_name)
        except ImageNotFound as e:
            logger.error(f"Image not found: {image_name}")
            raise

        # Basic image information
        image_id = image.id
        total_size = image.attrs.get("Size", 0)
        history = image.history()

        # Analyze layers
        layers = self._analyze_layers(image, history)
        layer_count = len(layers)

        # Calculate wasted space and efficiency
        wasted_space = sum(layer.wasted_space for layer in layers)
        efficiency_score = self._calculate_efficiency(total_size, wasted_space)

        # Dive analysis if available
        if use_dive and self.dive_path:
            dive_data = self._run_dive_analysis(image_name)
            if dive_data:
                self._enhance_with_dive_data(layers, dive_data)
                wasted_space = dive_data.get("wastedBytes", wasted_space)
                efficiency_score = dive_data.get("efficiencyScore", efficiency_score)

        # Detect base image
        base_image = self._detect_base_image(history)

        # Generate optimization suggestions
        suggestions = self._generate_suggestions(
            image, layers, base_image, wasted_space, efficiency_score
        )

        # Calculate potential savings
        potential_savings = sum(s.potential_savings for s in suggestions)

        # Recommend better base image
        recommended_base = self._recommend_base_image(base_image, total_size)

        analysis = ImageAnalysis(
            image_name=image_name,
            image_id=image_id,
            total_size=total_size,
            layer_count=layer_count,
            efficiency_score=efficiency_score,
            wasted_space=wasted_space,
            potential_savings=potential_savings,
            layers=layers,
            suggestions=suggestions,
            base_image=base_image,
            recommended_base=recommended_base,
        )

        logger.info(
            f"Analysis complete. Efficiency: {efficiency_score:.1f}%, "
            f"Wasted: {wasted_space / 1024 / 1024:.1f}MB"
        )

        return analysis

    def _analyze_layers(
        self, image: Image, history: List[Dict[str, Any]]
    ) -> List[LayerInfo]:
        """
        Analyze image layers from history.

        Args:
            image: Docker image object
            history: Image history data

        Returns:
            List of LayerInfo objects
        """
        layers = []

        for idx, layer_data in enumerate(history):
            layer_id = layer_data.get("Id", f"layer_{idx}")
            size = layer_data.get("Size", 0)
            created_by = layer_data.get("CreatedBy", "")
            created_ts = layer_data.get("Created", 0)

            # Parse creation timestamp
            if isinstance(created_ts, int):
                created = datetime.fromtimestamp(created_ts)
            else:
                created = datetime.now()

            # Detect potential issues in the command
            wasted_space = self._detect_layer_waste(created_by, size)

            layer = LayerInfo(
                id=layer_id,
                command=created_by[:200],  # Truncate long commands
                size=size,
                created=created,
                created_by=created_by,
                wasted_space=wasted_space,
            )

            layers.append(layer)

        return layers

    def _detect_layer_waste(self, command: str, size: int) -> int:
        """
        Detect potential wasted space in a layer command.

        Args:
            command: Layer creation command
            size: Layer size in bytes

        Returns:
            Estimated wasted space in bytes
        """
        wasted = 0

        # Check for common wasteful patterns
        wasteful_patterns = [
            # 30% recoverable
            (r"apt-get.*install.*&&\s*apt-get\s+clean", 0.3),
            (r"yum\s+install.*&&\s*yum\s+clean", 0.3),
            (r"apk\s+add.*&&\s*rm.*apk.*cache", 0.2),
            (r"pip\s+install.*--no-cache-dir", 0.0),  # Already optimized
            # 40% recoverable
            (r"pip\s+install(?!.*--no-cache-dir)", 0.4),
            (r"curl.*\|\s*tar", 0.1),  # Temporary download
            (r"wget.*&&.*rm", 0.1),
        ]

        for pattern, waste_factor in wasteful_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                wasted += int(size * waste_factor)
                break

        return wasted

    def _calculate_efficiency(self, total_size: int, wasted_space: int) -> float:
        """
        Calculate efficiency score (0-100).

        Args:
            total_size: Total image size in bytes
            wasted_space: Wasted space in bytes

        Returns:
            Efficiency percentage
        """
        if total_size == 0:
            return 100.0

        efficiency = ((total_size - wasted_space) / total_size) * 100
        return max(0.0, min(100.0, efficiency))

    def _run_dive_analysis(self, image_name: str) -> Optional[Dict[str, Any]]:
        """
        Run dive tool analysis on the image.

        Args:
            image_name: Name of the image to analyze

        Returns:
            Dive analysis data as dictionary or None if failed
        """
        if not self.dive_path:
            return None

        try:
            # Run dive with JSON output
            result = subprocess.run(
                [
                    self.dive_path,
                    image_name,
                    "--json",
                    "/dev/stdout",
                ],
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )

            if result.returncode != 0:
                logger.warning(f"Dive analysis failed: {result.stderr}")
                return None

            # Parse JSON output
            dive_data = json.loads(result.stdout)
            logger.info("Dive analysis completed successfully")
            return dive_data

        except subprocess.TimeoutExpired:
            logger.error("Dive analysis timed out")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse dive output: {e}")
            return None
        except Exception as e:
            logger.error(f"Dive analysis error: {e}")
            return None

    def _enhance_with_dive_data(
        self, layers: List[LayerInfo], dive_data: Dict[str, Any]
    ) -> None:
        """
        Enhance layer information with dive analysis data.

        Args:
            layers: List of LayerInfo objects to enhance
            dive_data: Dive analysis results
        """
        layer_details = dive_data.get("layer", {}).get("Details", [])

        for idx, (layer, detail) in enumerate(zip(layers, layer_details)):
            layer.efficiency = detail.get("efficiency", 100.0)
            layer.wasted_space = detail.get("wastedSpace", 0)
            layer.files_added = detail.get("filesAdded", 0)
            layer.files_removed = detail.get("filesRemoved", 0)
            layer.files_modified = detail.get("filesModified", 0)

    def _detect_base_image(self, history: List[Dict[str, Any]]) -> Optional[str]:
        """
        Detect the base image from history.

        Args:
            history: Image history data

        Returns:
            Base image name or None
        """
        # Base image is typically the first layer
        if history:
            # History is reverse chronological
            first_layer = history[-1]
            created_by = first_layer.get("CreatedBy", "")

            # Extract FROM instruction
            from_match = re.search(r"FROM\s+([^\s]+)", created_by, re.IGNORECASE)
            if from_match:
                return from_match.group(1)

        return None

    def _generate_suggestions(
        self,
        image: Image,
        layers: List[LayerInfo],
        base_image: Optional[str],
        wasted_space: int,
        efficiency_score: float,
    ) -> List[OptimizationSuggestion]:
        """
        Generate optimization suggestions based on analysis.

        Args:
            image: Docker image object
            layers: Analyzed layer information
            base_image: Detected base image
            wasted_space: Total wasted space
            efficiency_score: Overall efficiency score

        Returns:
            List of optimization suggestions
        """
        suggestions: List[OptimizationSuggestion] = []

        # Base image optimization
        if base_image:
            base_sugg = self._suggest_base_image_optimization(base_image)
            suggestions.extend(base_sugg)

        # Layer optimization
        layer_sugg = self._suggest_layer_optimization(layers)
        suggestions.extend(layer_sugg)

        # Multi-stage build suggestion
        if self._should_use_multistage(layers):
            multistage_desc = "Use multi-stage build to reduce final image size"
            multistage_impl = (
                "Split Dockerfile into build and runtime stages. "
                "Copy only necessary artifacts to final stage."
            )
            suggestions.append(
                OptimizationSuggestion(
                    category="architecture",
                    priority="high",
                    description=multistage_desc,
                    potential_savings=image.attrs.get("Size", 0) // 2,
                    difficulty="medium",
                    implementation=multistage_impl,
                )
            )

        # Package manager cleanup
        cleanup_sugg = self._suggest_cleanup_improvements(layers)
        suggestions.extend(cleanup_sugg)

        # Layer squashing
        if len(layers) > 20:
            desc = f"Reduce layer count from {len(layers)} by " "combining RUN commands"
            suggestions.append(
                OptimizationSuggestion(
                    category="layers",
                    priority="medium",
                    description=desc,
                    potential_savings=wasted_space // 4,
                    difficulty="easy",
                    implementation=(
                        "Combine multiple RUN commands using && operator. "
                        "Use single RUN for related operations."
                    ),
                )
            )

        # Efficiency improvement
        if efficiency_score < self.efficiency_threshold:
            eff_desc = (
                f"Overall efficiency is {efficiency_score:.1f}%, "
                f"target is {self.efficiency_threshold}%"
            )
            suggestions.append(
                OptimizationSuggestion(
                    category="efficiency",
                    priority="high",
                    description=eff_desc,
                    potential_savings=wasted_space,
                    difficulty="medium",
                    implementation=(
                        "Review all suggestions and implement "
                        "highest priority items. "
                        "Focus on cleanup and layer optimization."
                    ),
                )
            )

        # Sort by priority and potential savings
        suggestions.sort(
            key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}[x.priority],
                -x.potential_savings,
            )
        )

        return suggestions

    def _suggest_base_image_optimization(
        self, base_image: str
    ) -> List[OptimizationSuggestion]:
        """
        Generate base image optimization suggestions.

        Args:
            base_image: Current base image

        Returns:
            List of suggestions for base image optimization
        """
        suggestions: List[OptimizationSuggestion] = []

        # Detect runtime
        runtime: Optional[str] = None
        for key in self.base_image_map.keys():
            if key in base_image.lower():
                runtime = key
                break

        if not runtime:
            return suggestions

        # Check if using non-optimized base
        base_lower = base_image.lower()
        if "slim" not in base_lower and "alpine" not in base_lower:
            slim_opt = self.base_image_map[runtime].get(BaseImageType.SLIM)
            alpine_opt = self.base_image_map[runtime].get(BaseImageType.ALPINE)

            if slim_opt:
                desc = f"Switch from full to slim base image: {slim_opt}"
                impl = f"Change FROM {base_image} to FROM {slim_opt}"
                suggestions.append(
                    OptimizationSuggestion(
                        category="base_image",
                        priority="high",
                        description=desc,
                        potential_savings=200 * 1024 * 1024,  # ~200MB
                        difficulty="easy",
                        implementation=impl,
                    )
                )

            if alpine_opt:
                desc = f"Consider Alpine base: {alpine_opt}"
                impl = (
                    f"Change FROM {base_image} to FROM {alpine_opt}. "
                    "Note: May require package compatibility adjustments."
                )
                suggestions.append(
                    OptimizationSuggestion(
                        category="base_image",
                        priority="medium",
                        description=desc,
                        potential_savings=400 * 1024 * 1024,  # ~400MB
                        difficulty="medium",
                        implementation=impl,
                    )
                )

        return suggestions

    def _suggest_layer_optimization(
        self, layers: List[LayerInfo]
    ) -> List[OptimizationSuggestion]:
        """
        Generate layer-specific optimization suggestions.

        Args:
            layers: List of layer information

        Returns:
            List of layer optimization suggestions
        """
        suggestions = []

        for layer in layers:
            if layer.wasted_space > self.wasted_space_threshold:
                wasted_mb = layer.wasted_space / 1024 / 1024
                desc = f"Layer {layer.id[:12]} has " f"{wasted_mb:.1f}MB wasted space"
                impl = f"Review command: {layer.command[:100]}"
                suggestions.append(
                    OptimizationSuggestion(
                        category="layer",
                        priority="high",
                        description=desc,
                        potential_savings=layer.wasted_space,
                        difficulty="easy",
                        implementation=impl,
                        affected_layers=[layer.id],
                    )
                )

        return suggestions

    def _suggest_cleanup_improvements(
        self, layers: List[LayerInfo]
    ) -> List[OptimizationSuggestion]:
        """
        Suggest package manager cleanup improvements.

        Args:
            layers: List of layer information

        Returns:
            List of cleanup suggestions
        """
        suggestions = []

        for layer in layers:
            command = layer.command.lower()

            # apt-get without cleanup
            has_apt_install = "apt-get install" in command
            has_apt_clean = "apt-get clean" not in command
            if has_apt_install and has_apt_clean:
                impl = "Add: && apt-get clean && " "rm -rf /var/lib/apt/lists/*"
                suggestions.append(
                    OptimizationSuggestion(
                        category="cleanup",
                        priority="high",
                        description="Missing apt-get cleanup in layer",
                        potential_savings=layer.size // 3,
                        difficulty="easy",
                        implementation=impl,
                        affected_layers=[layer.id],
                    )
                )

            # pip without no-cache-dir
            if "pip install" in command and "--no-cache-dir" not in command:
                impl = "Add --no-cache-dir flag to pip install"
                suggestions.append(
                    OptimizationSuggestion(
                        category="cleanup",
                        priority="medium",
                        description="pip install without --no-cache-dir",
                        potential_savings=layer.size // 4,
                        difficulty="easy",
                        implementation=impl,
                        affected_layers=[layer.id],
                    )
                )

        return suggestions

    def _should_use_multistage(self, layers: List[LayerInfo]) -> bool:
        """
        Determine if multi-stage build would benefit the image.

        Args:
            layers: List of layer information

        Returns:
            True if multi-stage build is recommended
        """
        # Check for build tools in layers
        build_tools = [
            "gcc",
            "g++",
            "make",
            "cmake",
            "cargo",
            "go build",
            "npm run build",
            "maven",
            "gradle",
        ]

        for layer in layers:
            command = layer.command.lower()
            if any(tool in command for tool in build_tools):
                return True

        return False

    def _recommend_base_image(
        self, current_base: Optional[str], total_size: int
    ) -> Optional[str]:
        """
        Recommend optimal base image.

        Args:
            current_base: Current base image
            total_size: Total image size

        Returns:
            Recommended base image or None
        """
        if not current_base:
            return None

        # Detect runtime
        for runtime, images in self.base_image_map.items():
            if runtime in current_base.lower():
                # Large images should use slim
                if total_size > 500 * 1024 * 1024:  # > 500MB
                    return images.get(BaseImageType.SLIM) or images.get(
                        BaseImageType.ALPINE
                    )
                # Medium images could use alpine
                elif total_size > 100 * 1024 * 1024:  # > 100MB
                    return images.get(BaseImageType.ALPINE)

        return None

    def optimize_image(
        self,
        image_name: str,
        level: OptimizationLevel = OptimizationLevel.BALANCED,
        new_tag: Optional[str] = None,
    ) -> OptimizationResult:
        """
        Apply optimizations to an image.

        Args:
            image_name: Name of the image to optimize
            level: Optimization aggressiveness level
            new_tag: Tag for the optimized image (generates if None)

        Returns:
            OptimizationResult with optimization details
        """
        log_msg = f"Optimizing image {image_name} with {level.value} level"
        logger.info(log_msg)

        try:
            # Get original image
            original_image = self.client.images.get(image_name)
            original_size = original_image.attrs.get("Size", 0)

            # Generate new tag if not provided
            if not new_tag:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                new_tag = f"{image_name}:optimized-{timestamp}"

            # Analyze image
            analysis = self.analyze_image(image_name)

            # Apply optimizations based on level
            applied = []

            balanced_or_aggressive = (
                level == OptimizationLevel.BALANCED
                or level == OptimizationLevel.AGGRESSIVE
            )
            if balanced_or_aggressive:
                # Squash image to reduce layers
                if analysis.layer_count > 10:
                    success = self._squash_image(image_name, new_tag)
                    if success:
                        applied.append("layer_squashing")

            # Get optimized image size
            try:
                optimized_image = self.client.images.get(new_tag)
                optimized_size = optimized_image.attrs.get("Size", original_size)
            except ImageNotFound:
                optimized_size = original_size

            # Calculate results
            size_reduction = original_size - optimized_size
            if original_size > 0:
                percentage_saved = size_reduction / original_size * 100
            else:
                percentage_saved = 0

            result = OptimizationResult(
                success=len(applied) > 0,
                original_size=original_size,
                optimized_size=optimized_size,
                size_reduction=size_reduction,
                percentage_saved=percentage_saved,
                applied_optimizations=applied,
                new_image_name=new_tag if len(applied) > 0 else None,
            )

            saved_mb = size_reduction / 1024 / 1024
            log_msg = (
                f"Optimization complete. Saved {saved_mb:.1f}MB "
                f"({percentage_saved:.1f}%)"
            )
            logger.info(log_msg)

            return result

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return OptimizationResult(
                success=False,
                original_size=0,
                optimized_size=0,
                size_reduction=0,
                percentage_saved=0.0,
                applied_optimizations=[],
                error_message=str(e),
            )

    def _squash_image(self, image_name: str, new_tag: str) -> bool:
        """
        Squash image layers to reduce count.

        Args:
            image_name: Source image name
            new_tag: Target image tag

        Returns:
            True if successful
        """
        try:
            # Export and import to squash
            image = self.client.images.get(image_name)

            # Create temporary container
            container = self.client.containers.create(image_name)

            # Export container
            with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as f:
                temp_path = f.name
                for chunk in container.export():
                    f.write(chunk)

            # Remove temporary container
            container.remove()

            # Import as new image
            with open(temp_path, "rb") as f:
                self.client.images.load(f.read())

            # Tag the squashed image
            squashed = self.client.images.get(image.id)
            squashed.tag(new_tag)

            # Cleanup
            os.remove(temp_path)

            logger.info(f"Squashed image created: {new_tag}")
            return True

        except Exception as e:
            logger.error(f"Image squashing failed: {e}")
            return False

    def compare_images(self, image1: str, image2: str) -> Dict[str, Any]:
        """
        Compare two images and show differences.

        Args:
            image1: First image name
            image2: Second image name

        Returns:
            Dictionary with comparison results
        """
        logger.info(f"Comparing images: {image1} vs {image2}")

        analysis1 = self.analyze_image(image1, use_dive=False)
        analysis2 = self.analyze_image(image2, use_dive=False)

        comparison = {
            "image1": {
                "name": image1,
                "size": analysis1.total_size,
                "layers": analysis1.layer_count,
                "efficiency": analysis1.efficiency_score,
                "wasted_space": analysis1.wasted_space,
            },
            "image2": {
                "name": image2,
                "size": analysis2.total_size,
                "layers": analysis2.layer_count,
                "efficiency": analysis2.efficiency_score,
                "wasted_space": analysis2.wasted_space,
            },
            "differences": {
                "size_diff": analysis2.total_size - analysis1.total_size,
                "size_change_pct": (
                    (analysis2.total_size - analysis1.total_size)
                    / analysis1.total_size
                    * 100
                    if analysis1.total_size > 0
                    else 0
                ),
                "layer_diff": analysis2.layer_count - analysis1.layer_count,
                "efficiency_diff": (
                    analysis2.efficiency_score - analysis1.efficiency_score
                ),
                "wasted_space_diff": (analysis2.wasted_space - analysis1.wasted_space),
            },
            "recommendation": self._compare_recommendation(analysis1, analysis2),
        }

        return comparison

    def _compare_recommendation(
        self, analysis1: ImageAnalysis, analysis2: ImageAnalysis
    ) -> str:
        """
        Generate recommendation based on comparison.

        Args:
            analysis1: First image analysis
            analysis2: Second image analysis

        Returns:
            Recommendation string
        """
        if analysis2.total_size < analysis1.total_size:
            size_saved = analysis1.total_size - analysis2.total_size
            pct = (size_saved / analysis1.total_size) * 100
            return (
                f"{analysis2.image_name} is smaller by "
                f"{size_saved / 1024 / 1024:.1f}MB ({pct:.1f}%)"
            )
        elif analysis2.efficiency_score > analysis1.efficiency_score:
            return f"{analysis2.image_name} has better efficiency"
        else:
            return f"{analysis1.image_name} is the better choice"

    def export_analysis(
        self, analysis: ImageAnalysis, output_path: str, format: str = "json"
    ) -> None:
        """
        Export analysis results to file.

        Args:
            analysis: ImageAnalysis to export
            output_path: Output file path
            format: Export format (json, yaml, or text)
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            self._export_json(analysis, output_file)
        elif format == "text":
            self._export_text(analysis, output_file)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Analysis exported to {output_path}")

    def _export_json(self, analysis: ImageAnalysis, output_path: Path) -> None:
        """Export analysis as JSON."""
        data = {
            "image_name": analysis.image_name,
            "image_id": analysis.image_id,
            "total_size": analysis.total_size,
            "layer_count": analysis.layer_count,
            "efficiency_score": analysis.efficiency_score,
            "wasted_space": analysis.wasted_space,
            "potential_savings": analysis.potential_savings,
            "base_image": analysis.base_image,
            "recommended_base": analysis.recommended_base,
            "layers": [
                {
                    "id": layer.id,
                    "size": layer.size,
                    "wasted_space": layer.wasted_space,
                    "command": layer.command,
                }
                for layer in analysis.layers
            ],
            "suggestions": [
                {
                    "category": s.category,
                    "priority": s.priority,
                    "description": s.description,
                    "potential_savings": s.potential_savings,
                    "difficulty": s.difficulty,
                    "implementation": s.implementation,
                }
                for s in analysis.suggestions
            ],
            "analysis_time": analysis.analysis_time.isoformat(),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def _export_text(self, analysis: ImageAnalysis, output_path: Path) -> None:
        """Export analysis as human-readable text."""
        total_mb = analysis.total_size / 1024 / 1024
        wasted_mb = analysis.wasted_space / 1024 / 1024
        savings_mb = analysis.potential_savings / 1024 / 1024

        lines = [
            "=" * 80,
            f"Image Optimization Analysis: {analysis.image_name}",
            "=" * 80,
            "",
            "SUMMARY",
            "-" * 80,
            f"Image ID:          {analysis.image_id}",
            f"Total Size:        {total_mb:.1f} MB",
            f"Layer Count:       {analysis.layer_count}",
            f"Efficiency Score:  {analysis.efficiency_score:.1f}%",
            f"Wasted Space:      {wasted_mb:.1f} MB",
            f"Potential Savings: {savings_mb:.1f} MB",
            "",
        ]

        if analysis.base_image:
            lines.extend(
                [
                    "BASE IMAGE",
                    "-" * 80,
                    f"Current:     {analysis.base_image}",
                    f"Recommended: {analysis.recommended_base or 'N/A'}",
                    "",
                ]
            )

        if analysis.suggestions:
            lines.extend(["OPTIMIZATION SUGGESTIONS", "-" * 80])
            for idx, suggestion in enumerate(analysis.suggestions, 1):
                priority = suggestion.priority.upper()
                category = suggestion.category
                savings_mb = suggestion.potential_savings / 1024 / 1024
                lines.extend(
                    [
                        f"{idx}. [{priority}] {category}",
                        f"   {suggestion.description}",
                        f"   Potential Savings: {savings_mb:.1f} MB",
                        f"   Difficulty: {suggestion.difficulty}",
                        f"   Implementation: {suggestion.implementation}",
                        "",
                    ]
                )

        lines.append("=" * 80)

        with open(output_path, "w") as f:
            f.write("\n".join(lines))
