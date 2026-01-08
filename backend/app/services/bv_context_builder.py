"""Business View Context Builder - Extracts schema and metadata for LLM grounding."""

from typing import Dict, List, Set
from app.models.business_view import BusinessView
from app.core.logging import get_logger

logger = get_logger(__name__)


class BVContext:
    """Structured context extracted from Business View."""

    def __init__(
        self,
        schema_context: str,
        allowed_columns: Set[str],
        join_graph: Dict[str, List[str]],
        measures_info: Dict[str, Dict],
        dimensions_info: Dict[str, Dict],
        time_info: Dict,
    ):
        self.schema_context = schema_context
        self.allowed_columns = allowed_columns
        self.join_graph = join_graph
        self.measures_info = measures_info
        self.dimensions_info = dimensions_info
        self.time_info = time_info


class BVContextBuilder:
    """
    Extracts context from Business View for:
    1. LLM grounding (schema_context)
    2. SQL validation (allowed_columns)
    3. SQL construction (join_graph)
    4. Time semantics (time_info)
    """

    @staticmethod
    def build(business_view: BusinessView) -> BVContext:
        """
        Build complete context from Business View.

        Args:
            business_view: The Business View object

        Returns:
            BVContext with all extracted metadata
        """
        logger.info("building_bv_context", business_view_id=business_view.id)

        schema_context = BVContextBuilder._build_schema_context(business_view)
        allowed_columns = BVContextBuilder._extract_allowed_columns(business_view)
        join_graph = BVContextBuilder._build_join_graph(business_view)
        measures_info = BVContextBuilder._extract_measures_info(business_view)
        dimensions_info = BVContextBuilder._extract_dimensions_info(business_view)
        time_info = BVContextBuilder._extract_time_info(business_view)

        return BVContext(
            schema_context=schema_context,
            allowed_columns=allowed_columns,
            join_graph=join_graph,
            measures_info=measures_info,
            dimensions_info=dimensions_info,
            time_info=time_info,
        )

    @staticmethod
    def _build_schema_context(bv: BusinessView) -> str:
        """
        Build schema context string for LLM grounding.

        This provides the LLM with information about available tables,
        columns, measures, and dimensions.
        """
        context_parts = []

        # Business View overview
        context_parts.append(f"Business View: {bv.name}")
        context_parts.append(f"Description: {bv.description or 'N/A'}\n")

        # Tables and columns
        context_parts.append("Tables:")
        for table in bv.tables:
            context_parts.append(f"\n  {table.name} ({table.schema}):")
            for col in table.columns:
                context_parts.append(f"    - {col.name} ({col.type.value})")

        # Joins
        context_parts.append("\n\nJoin Relationships:")
        for join in bv.joins:
            context_parts.append(
                f"  {join.left_table}.{join.left_key} {join.join_type.value.upper()} JOIN "
                f"{join.right_table}.{join.right_key}"
            )

        # Measures
        context_parts.append("\n\nAvailable Measures (Metrics):")
        for measure in bv.measures:
            context_parts.append(f"  - {measure.name}: {measure.expression}")
            if measure.description:
                context_parts.append(f"      Description: {measure.description}")

        # Dimensions
        context_parts.append("\n\nAvailable Dimensions (Filters/Grouping):")
        for dim in bv.dimensions:
            context_parts.append(f"  - {dim.name}: {dim.table}.{dim.column}")
            if dim.description:
                context_parts.append(f"      Description: {dim.description}")

        # Time dimension
        context_parts.append("\n\nTime Dimension:")
        context_parts.append(
            f"  - Column: {bv.time_dimension.table}.{bv.time_dimension.column}"
        )
        context_parts.append(f"  - Granularity: {bv.time_dimension.granularity.value}")

        # Calendar rules
        context_parts.append("\n\nCalendar Rules:")
        context_parts.append(f"  - Fiscal year starts: Month {bv.calendar_rules.fiscal_year_start}")
        context_parts.append(f"  - Week starts: {bv.calendar_rules.week_start.value}")

        return "\n".join(context_parts)

    @staticmethod
    def _extract_allowed_columns(bv: BusinessView) -> Set[str]:
        """
        Extract set of all allowed fully-qualified column names.

        This is used for SQL validation to prevent SQL injection
        and ensure only valid columns are referenced.
        """
        allowed = set()

        # Add all table columns
        for table in bv.tables:
            for col in table.columns:
                allowed.add(f"{table.name}.{col.name}")

        # Add measure names (they can be referenced in queries)
        for measure in bv.measures:
            allowed.add(measure.name)

        # Add dimension names
        for dim in bv.dimensions:
            allowed.add(dim.name)
            allowed.add(f"{dim.table}.{dim.column}")

        # Add time dimension
        allowed.add(f"{bv.time_dimension.table}.{bv.time_dimension.column}")

        return allowed

    @staticmethod
    def _build_join_graph(bv: BusinessView) -> Dict[str, List[str]]:
        """
        Build join graph showing which tables connect to which.

        Returns:
            Dictionary mapping table name to list of connected tables
        """
        graph = {}

        for join in bv.joins:
            # Add edge from left to right
            if join.left_table not in graph:
                graph[join.left_table] = []
            graph[join.left_table].append({
                'table': join.right_table,
                'left_key': join.left_key,
                'right_key': join.right_key,
                'join_type': join.join_type.value,
            })

            # Add edge from right to left (for bidirectional traversal)
            if join.right_table not in graph:
                graph[join.right_table] = []
            graph[join.right_table].append({
                'table': join.left_table,
                'left_key': join.right_key,
                'right_key': join.left_key,
                'join_type': join.join_type.value,
            })

        return graph

    @staticmethod
    def _extract_measures_info(bv: BusinessView) -> Dict[str, Dict]:
        """Extract structured information about measures."""
        measures_info = {}

        for measure in bv.measures:
            measures_info[measure.name] = {
                'expression': measure.expression,
                'format': measure.format,
                'aggregation': measure.aggregation_function,
                'base_column': measure.base_column,
                'description': measure.description,
            }

        return measures_info

    @staticmethod
    def _extract_dimensions_info(bv: BusinessView) -> Dict[str, Dict]:
        """Extract structured information about dimensions."""
        dimensions_info = {}

        for dim in bv.dimensions:
            dimensions_info[dim.name] = {
                'column': dim.column,
                'table': dim.table,
                'full_name': dim.full_column_name,
                'description': dim.description,
            }

        return dimensions_info

    @staticmethod
    def _extract_time_info(bv: BusinessView) -> Dict:
        """Extract time dimension and calendar information."""
        return {
            'column': bv.time_dimension.column,
            'table': bv.time_dimension.table,
            'full_name': bv.time_dimension.full_column_name,
            'granularity': bv.time_dimension.granularity.value,
            'fiscal_year_start': bv.calendar_rules.fiscal_year_start,
            'week_start': bv.calendar_rules.week_start.value,
            'is_fiscal': bv.calendar_rules.is_fiscal_year(),
        }

    @staticmethod
    def get_table_for_measure(bv: BusinessView, measure_name: str) -> str:
        """
        Determine which table contains the base column for a measure.

        Args:
            bv: Business View
            measure_name: Name of the measure

        Returns:
            Table name containing the measure's base column
        """
        measure = bv.get_measure(measure_name)
        if not measure:
            raise ValueError(f"Measure '{measure_name}' not found in Business View")

        base_column = measure.base_column

        # Search for the column in tables
        for table in bv.tables:
            for col in table.columns:
                if col.name == base_column:
                    return table.name

        # If not found, assume it's in the fact table (first table typically)
        return bv.tables[0].name if bv.tables else None

    @staticmethod
    def get_required_joins(bv: BusinessView, tables_needed: List[str]) -> List[Dict]:
        """
        Determine minimum set of joins needed to connect specified tables.

        Args:
            bv: Business View
            tables_needed: List of table names to connect

        Returns:
            List of join specifications
        """
        if len(tables_needed) <= 1:
            return []

        # Simple approach: return all joins involving needed tables
        required_joins = []
        for join in bv.joins:
            if join.left_table in tables_needed or join.right_table in tables_needed:
                required_joins.append({
                    'left_table': join.left_table,
                    'right_table': join.right_table,
                    'left_key': join.left_key,
                    'right_key': join.right_key,
                    'join_type': join.join_type.value,
                })

        return required_joins
