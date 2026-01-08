#!/usr/bin/env python3
"""
Verification script for TQL services.

This script performs basic sanity checks to ensure all three services
(TQLPlanner, PlanValidator, TQLAdapter) are working correctly.
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.business_view import (
    BusinessView,
    Table,
    Column,
    ColumnType,
    Join,
    JoinType,
    Measure,
    Dimension,
    TimeDimension,
    CalendarRules,
    Granularity,
)
from app.models.intent import (
    ParsedIntent,
    TimeRange,
    BaselineConfig,
    BaselineType,
    FeedType,
)
from app.services.bv_context_builder import BVContextBuilder
from app.services.tql_planner import TQLPlanner
from app.services.plan_validator import PlanValidator, ValidationError


def create_test_business_view() -> BusinessView:
    """Create a minimal Business View for testing."""
    return BusinessView(
        id="test_bv",
        name="Test Business View",
        tables=[
            Table(
                name="sales",
                columns=[
                    Column(name="id", type=ColumnType.INTEGER),
                    Column(name="date", type=ColumnType.DATE),
                    Column(name="revenue", type=ColumnType.FLOAT),
                ],
            ),
        ],
        joins=[],
        measures=[
            Measure(
                name="Total Revenue",
                expression="SUM(revenue)",
                format="currency",
            ),
        ],
        dimensions=[],
        time_dimension=TimeDimension(
            column="date",
            table="sales",
            granularity=Granularity.DAY,
        ),
        calendar_rules=CalendarRules(),
    )


def check_imports():
    """Verify all required modules can be imported."""
    print("Checking imports...")
    try:
        from app.services import (
            TQLPlanner,
            PlanValidator,
            TQLAdapter,
            BVContextBuilder,
        )
        print("  ✓ All services imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def check_tql_planner():
    """Verify TQLPlanner works correctly."""
    print("\nChecking TQLPlanner...")
    try:
        bv = create_test_business_view()
        intent = ParsedIntent(
            metric="Total Revenue",
            time_range=TimeRange(
                start_date=date.today() - timedelta(days=30),
                end_date=date.today(),
            ),
            filters={},
        )

        plan = TQLPlanner.generate(intent, bv)

        # Verify plan structure
        assert plan is not None, "Plan is None"
        assert plan.current_period_query is not None, "Current period query missing"
        assert "SELECT" in plan.current_period_query, "Invalid SQL"
        assert "SUM(revenue)" in plan.current_period_query, "Measure missing"

        print("  ✓ TQLPlanner generates valid plans")
        print(f"  ✓ Complexity score: {plan.metadata.complexity_score}/10")
        return True

    except Exception as e:
        print(f"  ✗ TQLPlanner failed: {e}")
        return False


def check_plan_validator():
    """Verify PlanValidator works correctly."""
    print("\nChecking PlanValidator...")
    try:
        bv = create_test_business_view()
        bv_context = BVContextBuilder.build(bv)

        intent = ParsedIntent(
            metric="Total Revenue",
            time_range=TimeRange(
                start_date=date.today() - timedelta(days=30),
                end_date=date.today(),
            ),
            filters={},
        )

        plan = TQLPlanner.generate(intent, bv)

        # Should validate successfully
        validated_plan = PlanValidator.validate(plan, bv_context)
        assert validated_plan is plan, "Plan validation failed"

        print("  ✓ PlanValidator accepts safe queries")

        # Test security checks
        from app.models.plan import TQLPlan, PlanMetadata

        dangerous_plan = TQLPlan(
            current_period_query="DROP TABLE sales",
            metadata=PlanMetadata(),
        )

        try:
            PlanValidator.validate(dangerous_plan, bv_context)
            print("  ✗ PlanValidator failed to reject dangerous query")
            return False
        except ValidationError:
            print("  ✓ PlanValidator rejects dangerous queries")

        return True

    except Exception as e:
        print(f"  ✗ PlanValidator failed: {e}")
        return False


def check_tql_adapter():
    """Verify TQLAdapter basic functionality."""
    print("\nChecking TQLAdapter...")
    try:
        from app.services.tql_adapter import TQLAdapter
        import tempfile
        import os

        # Create temporary database
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)

        adapter = TQLAdapter(f"sqlite:///{db_path}")

        # Test connection
        if not adapter.test_connection():
            print("  ✗ Database connection failed")
            return False

        print("  ✓ TQLAdapter connects to database")

        # Clean up
        os.unlink(db_path)

        return True

    except Exception as e:
        print(f"  ✗ TQLAdapter failed: {e}")
        return False


def check_integration():
    """Verify all services work together."""
    print("\nChecking integration...")
    try:
        bv = create_test_business_view()
        bv_context = BVContextBuilder.build(bv)

        intent = ParsedIntent(
            metric="Total Revenue",
            time_range=TimeRange(
                start_date=date.today() - timedelta(days=30),
                end_date=date.today(),
            ),
            filters={},
            baseline=BaselineConfig(type=BaselineType.PREVIOUS_PERIOD),
        )

        # Generate plan
        plan = TQLPlanner.generate(intent, bv)
        assert plan is not None, "Plan generation failed"

        # Validate plan
        validated_plan = PlanValidator.validate(plan, bv_context)
        assert validated_plan is plan, "Plan validation failed"

        print("  ✓ Full pipeline (Generate → Validate) works")
        return True

    except Exception as e:
        print(f"  ✗ Integration failed: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("TQL Services Verification")
    print("=" * 70)

    checks = [
        ("Imports", check_imports),
        ("TQLPlanner", check_tql_planner),
        ("PlanValidator", check_plan_validator),
        ("TQLAdapter", check_tql_adapter),
        ("Integration", check_integration),
    ]

    results = []
    for name, check_func in checks:
        success = check_func()
        results.append((name, success))

    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)

    all_passed = True
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{name:20s} {status}")
        if not success:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n✓ All checks passed! TQL services are working correctly.")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
