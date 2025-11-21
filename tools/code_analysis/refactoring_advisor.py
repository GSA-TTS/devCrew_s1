"""
Refactoring Advisor Module.

Suggests refactoring opportunities based on code analysis results,
mapping code smells and complexity issues to appropriate refactoring patterns.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional


class RefactoringType(Enum):
    """Types of refactoring patterns."""

    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    INLINE_METHOD = "inline_method"
    MOVE_METHOD = "move_method"
    RENAME = "rename"
    INTRODUCE_PARAMETER_OBJECT = "introduce_parameter_object"
    REPLACE_CONDITIONAL_WITH_POLYMORPHISM = "replace_conditional_with_polymorphism"
    DECOMPOSE_CONDITIONAL = "decompose_conditional"
    CONSOLIDATE_CONDITIONAL = "consolidate_conditional"
    REPLACE_MAGIC_NUMBER = "replace_magic_number"
    ENCAPSULATE_FIELD = "encapsulate_field"
    REPLACE_TEMP_WITH_QUERY = "replace_temp_with_query"
    SPLIT_LOOP = "split_loop"
    GUARD_CLAUSE = "guard_clause"
    STRATEGY_PATTERN = "strategy_pattern"
    BUILDER_PATTERN = "builder_pattern"


@dataclass
class RefactoringSuggestion:
    """A refactoring suggestion."""

    refactoring_type: RefactoringType
    title: str
    description: str
    location: str
    lineno: int
    impact: str  # low, medium, high
    effort: str  # low, medium, high
    steps: List[str] = field(default_factory=list)
    code_example: str = ""
    source_smell: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "refactoring_type": self.refactoring_type.value,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "lineno": self.lineno,
            "impact": self.impact,
            "effort": self.effort,
            "steps": self.steps,
            "code_example": self.code_example,
            "source_smell": self.source_smell,
        }


class RefactoringAdvisor:
    """Suggests refactoring opportunities based on analysis results."""

    # Mapping of code smells to refactoring patterns
    SMELL_TO_REFACTORING: Dict[str, List[RefactoringType]] = {
        "long_method": [
            RefactoringType.EXTRACT_METHOD,
            RefactoringType.DECOMPOSE_CONDITIONAL,
        ],
        "large_class": [
            RefactoringType.EXTRACT_CLASS,
            RefactoringType.MOVE_METHOD,
        ],
        "god_class": [
            RefactoringType.EXTRACT_CLASS,
            RefactoringType.MOVE_METHOD,
            RefactoringType.STRATEGY_PATTERN,
        ],
        "too_many_parameters": [
            RefactoringType.INTRODUCE_PARAMETER_OBJECT,
            RefactoringType.BUILDER_PATTERN,
        ],
        "deep_nesting": [
            RefactoringType.GUARD_CLAUSE,
            RefactoringType.EXTRACT_METHOD,
            RefactoringType.DECOMPOSE_CONDITIONAL,
        ],
        "feature_envy": [
            RefactoringType.MOVE_METHOD,
            RefactoringType.EXTRACT_METHOD,
        ],
        "too_many_branches": [
            RefactoringType.REPLACE_CONDITIONAL_WITH_POLYMORPHISM,
            RefactoringType.STRATEGY_PATTERN,
            RefactoringType.DECOMPOSE_CONDITIONAL,
        ],
        "too_many_returns": [
            RefactoringType.GUARD_CLAUSE,
            RefactoringType.CONSOLIDATE_CONDITIONAL,
        ],
        "too_many_variables": [
            RefactoringType.EXTRACT_METHOD,
            RefactoringType.REPLACE_TEMP_WITH_QUERY,
        ],
        "too_many_methods": [
            RefactoringType.EXTRACT_CLASS,
        ],
        "too_many_attributes": [
            RefactoringType.EXTRACT_CLASS,
            RefactoringType.ENCAPSULATE_FIELD,
        ],
        "cyclomatic_complexity": [
            RefactoringType.DECOMPOSE_CONDITIONAL,
            RefactoringType.EXTRACT_METHOD,
            RefactoringType.REPLACE_CONDITIONAL_WITH_POLYMORPHISM,
        ],
        "cognitive_complexity": [
            RefactoringType.EXTRACT_METHOD,
            RefactoringType.GUARD_CLAUSE,
            RefactoringType.DECOMPOSE_CONDITIONAL,
        ],
    }

    # Detailed guidance for each refactoring type
    REFACTORING_GUIDANCE: Dict[RefactoringType, Dict[str, Any]] = {
        RefactoringType.EXTRACT_METHOD: {
            "description": (
                "Extract a fragment of code into its own method with a "
                "descriptive name"
            ),
            "impact": "high",
            "effort": "low",
            "steps": [
                "Identify code fragment that can be grouped",
                "Create new method with descriptive name",
                "Move code to new method",
                "Replace original code with method call",
                "Pass needed variables as parameters",
                "Update tests",
            ],
            "example": """
# Before
def process_order(order):
    # Calculate total
    total = 0
    for item in order.items:
        total += item.price * item.quantity
    total *= (1 - order.discount)
    # ... more code

# After
def process_order(order):
    total = calculate_total(order)
    # ... more code

def calculate_total(order):
    subtotal = sum(item.price * item.quantity for item in order.items)
    return subtotal * (1 - order.discount)
""",
        },
        RefactoringType.EXTRACT_CLASS: {
            "description": (
                "Move related fields and methods to a new class when a class "
                "is doing too much"
            ),
            "impact": "high",
            "effort": "medium",
            "steps": [
                "Identify related fields and methods",
                "Create new class for extracted behavior",
                "Move fields and methods to new class",
                "Update original class to use new class",
                "Update all references",
                "Update tests",
            ],
            "example": """
# Before
class Order:
    def __init__(self):
        self.customer_name = ""
        self.customer_email = ""
        self.customer_phone = ""
        self.items = []

# After
class Customer:
    def __init__(self, name, email, phone):
        self.name = name
        self.email = email
        self.phone = phone

class Order:
    def __init__(self, customer):
        self.customer = customer
        self.items = []
""",
        },
        RefactoringType.INTRODUCE_PARAMETER_OBJECT: {
            "description": (
                "Replace a group of parameters with a single object"
            ),
            "impact": "medium",
            "effort": "low",
            "steps": [
                "Create a class/dataclass for the parameter group",
                "Update method signature to use the new type",
                "Update all callers",
                "Consider adding behavior to the new class",
            ],
            "example": """
# Before
def create_user(name, email, phone, address, city, country):
    pass

# After
@dataclass
class UserInfo:
    name: str
    email: str
    phone: str
    address: str
    city: str
    country: str

def create_user(user_info: UserInfo):
    pass
""",
        },
        RefactoringType.GUARD_CLAUSE: {
            "description": (
                "Replace nested conditionals with guard clauses that return "
                "early"
            ),
            "impact": "medium",
            "effort": "low",
            "steps": [
                "Identify nested conditionals",
                "Convert to guard clauses with early returns",
                "Ensure each guard handles one specific case",
                "Test edge cases",
            ],
            "example": """
# Before
def get_payment(order):
    if order:
        if order.is_valid:
            if order.items:
                return calculate_payment(order)
    return 0

# After
def get_payment(order):
    if not order:
        return 0
    if not order.is_valid:
        return 0
    if not order.items:
        return 0
    return calculate_payment(order)
""",
        },
        RefactoringType.REPLACE_CONDITIONAL_WITH_POLYMORPHISM: {
            "description": (
                "Replace complex conditionals with polymorphic behavior"
            ),
            "impact": "high",
            "effort": "high",
            "steps": [
                "Create an abstract base class or protocol",
                "Create subclass for each conditional branch",
                "Move branch logic to subclass method",
                "Replace conditional with polymorphic call",
                "Update object creation to use factory if needed",
            ],
            "example": """
# Before
def calculate_shipping(order):
    if order.type == "standard":
        return order.weight * 1.5
    elif order.type == "express":
        return order.weight * 3.0
    elif order.type == "overnight":
        return order.weight * 5.0

# After
class ShippingCalculator(ABC):
    @abstractmethod
    def calculate(self, order): pass

class StandardShipping(ShippingCalculator):
    def calculate(self, order):
        return order.weight * 1.5

class ExpressShipping(ShippingCalculator):
    def calculate(self, order):
        return order.weight * 3.0
""",
        },
        RefactoringType.MOVE_METHOD: {
            "description": (
                "Move a method to a class that uses it more"
            ),
            "impact": "medium",
            "effort": "medium",
            "steps": [
                "Identify the method's primary data dependencies",
                "Move method to the class with most dependencies",
                "Update the original class to delegate if needed",
                "Update all callers",
            ],
            "example": """
# Before (in OrderProcessor)
def calculate_discount(self, customer):
    return customer.orders_count * 0.01

# After (in Customer)
def calculate_discount(self):
    return self.orders_count * 0.01
""",
        },
        RefactoringType.DECOMPOSE_CONDITIONAL: {
            "description": (
                "Extract condition and branches into separate methods"
            ),
            "impact": "medium",
            "effort": "low",
            "steps": [
                "Extract condition into a method with descriptive name",
                "Extract then-branch into a method",
                "Extract else-branch into a method",
            ],
            "example": """
# Before
if date < SUMMER_START or date > SUMMER_END:
    charge = quantity * winter_rate + winter_service_charge
else:
    charge = quantity * summer_rate

# After
if is_winter(date):
    charge = winter_charge(quantity)
else:
    charge = summer_charge(quantity)
""",
        },
        RefactoringType.STRATEGY_PATTERN: {
            "description": (
                "Define a family of algorithms and make them interchangeable"
            ),
            "impact": "high",
            "effort": "high",
            "steps": [
                "Define strategy interface",
                "Create concrete strategy classes",
                "Add strategy field to context class",
                "Replace conditional logic with strategy calls",
            ],
            "example": """
# Strategy interface
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, base_price): pass

# Concrete strategies
class RegularPricing(PricingStrategy):
    def calculate_price(self, base_price):
        return base_price

class PremiumPricing(PricingStrategy):
    def calculate_price(self, base_price):
        return base_price * 0.9

# Context
class Order:
    def __init__(self, pricing_strategy):
        self.pricing_strategy = pricing_strategy

    def get_price(self):
        return self.pricing_strategy.calculate_price(self.base_price)
""",
        },
        RefactoringType.BUILDER_PATTERN: {
            "description": (
                "Use a builder to construct complex objects step by step"
            ),
            "impact": "medium",
            "effort": "medium",
            "steps": [
                "Create builder class with fluent interface",
                "Add methods for each construction step",
                "Add build() method that returns the final object",
                "Update object creation to use builder",
            ],
            "example": """
# Builder
class UserBuilder:
    def __init__(self):
        self._name = ""
        self._email = ""

    def with_name(self, name):
        self._name = name
        return self

    def with_email(self, email):
        self._email = email
        return self

    def build(self):
        return User(self._name, self._email)

# Usage
user = UserBuilder().with_name("John").with_email("john@example.com").build()
""",
        },
        RefactoringType.REPLACE_TEMP_WITH_QUERY: {
            "description": (
                "Replace a temporary variable with a method call"
            ),
            "impact": "low",
            "effort": "low",
            "steps": [
                "Identify temporary variable used multiple times",
                "Extract computation to a method",
                "Replace variable with method calls",
            ],
            "example": """
# Before
base_price = quantity * item_price
if base_price > 1000:
    return base_price * 0.95
return base_price

# After
def base_price(self):
    return self.quantity * self.item_price

if self.base_price() > 1000:
    return self.base_price() * 0.95
return self.base_price()
""",
        },
        RefactoringType.CONSOLIDATE_CONDITIONAL: {
            "description": (
                "Combine conditional branches that have the same result"
            ),
            "impact": "low",
            "effort": "low",
            "steps": [
                "Identify conditionals with same result",
                "Combine conditions with logical operators",
                "Extract to method if complex",
            ],
            "example": """
# Before
if is_weekend:
    return 0
if is_holiday:
    return 0
if is_vacation:
    return 0

# After
def is_not_working_day():
    return is_weekend or is_holiday or is_vacation

if is_not_working_day():
    return 0
""",
        },
        RefactoringType.ENCAPSULATE_FIELD: {
            "description": (
                "Make a field private and provide getter/setter methods"
            ),
            "impact": "low",
            "effort": "low",
            "steps": [
                "Create getter and setter methods",
                "Make field private (prefix with _)",
                "Update all direct accesses to use methods",
                "Consider using @property decorator",
            ],
            "example": """
# Before
class Account:
    def __init__(self):
        self.balance = 0

# After
class Account:
    def __init__(self):
        self._balance = 0

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        if value < 0:
            raise ValueError("Balance cannot be negative")
        self._balance = value
""",
        },
        RefactoringType.INLINE_METHOD: {
            "description": (
                "Replace a method call with its body when the method is trivial"
            ),
            "impact": "low",
            "effort": "low",
            "steps": [
                "Copy method body to caller",
                "Replace all calls with method body",
                "Remove the method",
            ],
            "example": """
# Before
def get_rating():
    return more_than_five_late_deliveries()

def more_than_five_late_deliveries():
    return late_deliveries > 5

# After
def get_rating():
    return late_deliveries > 5
""",
        },
        RefactoringType.RENAME: {
            "description": (
                "Rename a variable, method, or class to better describe "
                "its purpose"
            ),
            "impact": "medium",
            "effort": "low",
            "steps": [
                "Choose a descriptive name",
                "Update the declaration",
                "Update all references",
                "Update tests and documentation",
            ],
            "example": """
# Before
def calc(d):
    return d * 1.1

# After
def calculate_price_with_tax(base_price):
    return base_price * 1.1
""",
        },
        RefactoringType.SPLIT_LOOP: {
            "description": (
                "Split a loop that does multiple things into separate loops"
            ),
            "impact": "low",
            "effort": "low",
            "steps": [
                "Identify distinct operations in the loop",
                "Duplicate the loop",
                "Remove different operations from each loop",
            ],
            "example": """
# Before
total = 0
average = 0
for item in items:
    total += item.value
    average += item.rating
average = average / len(items)

# After
total = sum(item.value for item in items)
average = sum(item.rating for item in items) / len(items)
""",
        },
    }

    def __init__(self) -> None:
        """Initialize the refactoring advisor."""
        pass

    def analyze(
        self,
        smells: List[Dict[str, Any]],
        complexity_violations: Optional[List[Dict[str, Any]]] = None,
    ) -> List[RefactoringSuggestion]:
        """
        Analyze code smells and violations to suggest refactorings.

        Args:
            smells: List of detected code smells
            complexity_violations: Optional list of complexity violations

        Returns:
            List of refactoring suggestions
        """
        suggestions = []
        complexity_violations = complexity_violations or []

        # Process code smells
        for smell in smells:
            smell_name = smell.get("name", "")
            if smell_name in self.SMELL_TO_REFACTORING:
                refactoring_types = self.SMELL_TO_REFACTORING[smell_name]
                for ref_type in refactoring_types:
                    suggestion = self._create_suggestion(
                        ref_type, smell, smell_name
                    )
                    if suggestion:
                        suggestions.append(suggestion)

        # Process complexity violations
        for violation in complexity_violations:
            vtype = violation.get("type", "")
            if vtype in self.SMELL_TO_REFACTORING:
                refactoring_types = self.SMELL_TO_REFACTORING[vtype]
                for ref_type in refactoring_types:
                    suggestion = self._create_suggestion(
                        ref_type,
                        {
                            "location": violation.get("file", "unknown"),
                            "lineno": violation.get("lineno", 0),
                            "description": (
                                f"{violation.get('function', 'Unknown')} has "
                                f"{vtype} of {violation.get('value')}"
                            ),
                        },
                        vtype,
                    )
                    if suggestion:
                        suggestions.append(suggestion)

        # Remove duplicates based on location and type
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            key = (s.location, s.lineno, s.refactoring_type)
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(s)

        return unique_suggestions

    def get_refactoring_guidance(
        self,
        refactoring_type: RefactoringType,
    ) -> Dict[str, Any]:
        """
        Get detailed guidance for a specific refactoring type.

        Args:
            refactoring_type: The type of refactoring

        Returns:
            Dictionary with guidance details
        """
        guidance = self.REFACTORING_GUIDANCE.get(refactoring_type, {})
        return {
            "type": refactoring_type.value,
            **guidance,
        }

    def suggest_for_smell(self, smell_name: str) -> List[RefactoringType]:
        """
        Get recommended refactoring types for a specific smell.

        Args:
            smell_name: Name of the code smell

        Returns:
            List of applicable refactoring types
        """
        return self.SMELL_TO_REFACTORING.get(smell_name, [])

    def _create_suggestion(
        self,
        ref_type: RefactoringType,
        context: Dict[str, Any],
        source_smell: str,
    ) -> Optional[RefactoringSuggestion]:
        """Create a refactoring suggestion from context."""
        guidance = self.REFACTORING_GUIDANCE.get(ref_type)
        if not guidance:
            return None

        return RefactoringSuggestion(
            refactoring_type=ref_type,
            title=f"Apply {ref_type.value.replace('_', ' ').title()}",
            description=guidance["description"],
            location=context.get("location", ""),
            lineno=context.get("lineno", 0),
            impact=guidance.get("impact", "medium"),
            effort=guidance.get("effort", "medium"),
            steps=guidance.get("steps", []),
            code_example=guidance.get("example", ""),
            source_smell=source_smell,
        )

    def to_dict(
        self,
        suggestions: List[RefactoringSuggestion],
    ) -> Dict[str, Any]:
        """Convert suggestions to dictionary format."""
        return {
            "suggestions": [s.to_dict() for s in suggestions],
            "summary": {
                "total": len(suggestions),
                "by_type": self._count_by_type(suggestions),
                "by_impact": self._count_by_impact(suggestions),
                "by_effort": self._count_by_effort(suggestions),
            },
        }

    def _count_by_type(
        self,
        suggestions: List[RefactoringSuggestion],
    ) -> Dict[str, int]:
        """Count suggestions by refactoring type."""
        counts: Dict[str, int] = {}
        for s in suggestions:
            key = s.refactoring_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _count_by_impact(
        self,
        suggestions: List[RefactoringSuggestion],
    ) -> Dict[str, int]:
        """Count suggestions by impact."""
        counts: Dict[str, int] = {}
        for s in suggestions:
            counts[s.impact] = counts.get(s.impact, 0) + 1
        return counts

    def _count_by_effort(
        self,
        suggestions: List[RefactoringSuggestion],
    ) -> Dict[str, int]:
        """Count suggestions by effort."""
        counts: Dict[str, int] = {}
        for s in suggestions:
            counts[s.effort] = counts.get(s.effort, 0) + 1
        return counts
