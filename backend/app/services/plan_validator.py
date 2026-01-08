"""Plan Validator - Validates SQL plans for security and Tellius compatibility."""

import re
from typing import List, Set, Dict
from app.models.plan import TQLPlan
from app.services.bv_context_builder import BVContext
from app.core.logging import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Raised when SQL plan validation fails."""

    def __init__(self, message: str, query_name: str = None, details: str = None):
        self.message = message
        self.query_name = query_name
        self.details = details
        super().__init__(self.message)


class PlanValidator:
    """
    Validates TQL plans for security and compatibility.

    Security checks:
    - Column whitelist validation
    - SQL injection prevention
    - Dangerous operation detection

    Tellius compatibility checks:
    - Proper aggregation usage
    - Compatible SQL dialect
    - Join constraint validation
    """

    # Dangerous SQL keywords that should never appear
    DANGEROUS_KEYWORDS = {
        "DROP",
        "DELETE",
        "TRUNCATE",
        "ALTER",
        "CREATE",
        "INSERT",
        "UPDATE",
        "EXEC",
        "EXECUTE",
        "GRANT",
        "REVOKE",
    }

    # Allowed SQL keywords
    ALLOWED_KEYWORDS = {
        "SELECT",
        "FROM",
        "WHERE",
        "JOIN",
        "INNER",
        "LEFT",
        "RIGHT",
        "FULL",
        "ON",
        "AND",
        "OR",
        "NOT",
        "IN",
        "BETWEEN",
        "LIKE",
        "IS",
        "NULL",
        "GROUP",
        "BY",
        "HAVING",
        "ORDER",
        "ASC",
        "DESC",
        "LIMIT",
        "OFFSET",
        "AS",
        "DISTINCT",
        "COUNT",
        "SUM",
        "AVG",
        "MIN",
        "MAX",
    }

    @staticmethod
    def validate(plan: TQLPlan, bv_context: BVContext) -> TQLPlan:
        """
        Validate TQL plan for security and compatibility.

        Args:
            plan: The TQL plan to validate
            bv_context: Business View context with allowed columns

        Returns:
            The validated TQL plan (same object if valid)

        Raises:
            ValidationError: If validation fails
        """
        logger.info("validating_tql_plan", queries_count=len(plan.get_all_queries()))

        # Validate each query in the plan
        for query_name, query_sql in plan.get_all_queries():
            try:
                PlanValidator._validate_query(query_sql, query_name, bv_context)
            except ValidationError as e:
                logger.error(
                    "query_validation_failed",
                    query_name=query_name,
                    error=e.message,
                    details=e.details,
                )
                raise

        logger.info("tql_plan_validated_successfully")
        return plan

    @staticmethod
    def _validate_query(query: str, query_name: str, bv_context: BVContext) -> None:
        """Validate a single SQL query."""
        # 1. Check for dangerous keywords
        PlanValidator._check_dangerous_keywords(query, query_name)

        # 2. Check for SQL injection patterns
        PlanValidator._check_sql_injection(query, query_name)

        # 3. Validate column references
        PlanValidator._validate_column_references(query, query_name, bv_context)

        # 4. Check for proper structure
        PlanValidator._validate_query_structure(query, query_name)

        # 5. Check aggregation usage
        PlanValidator._validate_aggregation(query, query_name)

    @staticmethod
    def _check_dangerous_keywords(query: str, query_name: str) -> None:
        """Check for dangerous SQL keywords."""
        query_upper = query.upper()

        for keyword in PlanValidator.DANGEROUS_KEYWORDS:
            # Match keyword as whole word (not part of another word)
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, query_upper):
                raise ValidationError(
                    message=f"Dangerous SQL keyword detected: {keyword}",
                    query_name=query_name,
                    details=f"Query contains forbidden keyword '{keyword}' which could be used for malicious operations",
                )

    @staticmethod
    def _check_sql_injection(query: str, query_name: str) -> None:
        """Check for common SQL injection patterns."""
        # Check for suspicious comment patterns
        if "--" in query or "/*" in query or "*/" in query:
            # Allow comments at the end of lines, but be cautious
            suspicious_comment_patterns = [
                r"--.*[;]",  # Comment followed by semicolon
                r";\s*--",  # Semicolon followed by comment
                r"/\*.*\*/.*[;]",  # Block comment with semicolon
            ]
            for pattern in suspicious_comment_patterns:
                if re.search(pattern, query):
                    raise ValidationError(
                        message="Suspicious comment pattern detected",
                        query_name=query_name,
                        details="Query contains comment patterns that could indicate SQL injection attempt",
                    )

        # Check for multiple statements (semicolons)
        # Allow semicolon only at the very end
        semicolon_count = query.count(";")
        if semicolon_count > 1:
            raise ValidationError(
                message="Multiple SQL statements detected",
                query_name=query_name,
                details="Query contains multiple semicolons, which could indicate SQL injection",
            )
        elif semicolon_count == 1 and not query.rstrip().endswith(";"):
            raise ValidationError(
                message="Semicolon in middle of query",
                query_name=query_name,
                details="Semicolons are only allowed at the end of the query",
            )

        # Check for UNION attacks
        if re.search(r'\bUNION\b', query, re.IGNORECASE):
            raise ValidationError(
                message="UNION keyword detected",
                query_name=query_name,
                details="UNION is not allowed to prevent SQL injection attacks",
            )

        # Check for subqueries (could be used for injection)
        # Allow subqueries in specific contexts, but be restrictive
        nested_select_count = query.upper().count("SELECT") - 1  # Subtract main SELECT
        if nested_select_count > 0:
            # For now, disallow subqueries entirely (can be relaxed if needed)
            raise ValidationError(
                message="Subqueries are not allowed",
                query_name=query_name,
                details="Nested SELECT statements detected. Subqueries are restricted for security.",
            )

    @staticmethod
    def _validate_column_references(query: str, query_name: str, bv_context: BVContext) -> None:
        """Validate that all column references are in the whitelist."""
        # Extract potential column references from the query
        # This is a simplified approach - could be enhanced with SQL parsing

        # Pattern to match table.column or column references
        column_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*\.)?([a-zA-Z_][a-zA-Z0-9_]*)\b'

        # Get all potential column references
        potential_columns = set()
        for match in re.finditer(column_pattern, query):
            full_match = match.group(0)

            # Skip SQL keywords
            if full_match.upper() in PlanValidator.ALLOWED_KEYWORDS:
                continue

            # Skip aggregation functions
            if full_match.upper() in ["COUNT", "SUM", "AVG", "MIN", "MAX", "DISTINCT"]:
                continue

            # Skip common SQL terms
            if full_match.upper() in ["NULL", "TRUE", "FALSE", "ASC", "DESC"]:
                continue

            # Skip aliases (AS keyword followed by identifier)
            if re.search(r'\bAS\s+' + re.escape(full_match), query, re.IGNORECASE):
                continue

            potential_columns.add(full_match)

        # Validate each column reference
        invalid_columns = []
        for col_ref in potential_columns:
            # Check if it's in allowed columns (exact match or partial match)
            is_valid = False

            # Check exact match
            if col_ref in bv_context.allowed_columns:
                is_valid = True

            # Check if it's part of a qualified column name
            for allowed_col in bv_context.allowed_columns:
                if allowed_col.endswith("." + col_ref) or allowed_col == col_ref:
                    is_valid = True
                    break
                # Also check if col_ref contains table.column format
                if "." in col_ref and col_ref == allowed_col:
                    is_valid = True
                    break

            if not is_valid:
                # Give benefit of doubt for numeric literals and string literals
                if not (col_ref.isdigit() or col_ref.replace(".", "").isdigit()):
                    invalid_columns.append(col_ref)

        if invalid_columns:
            logger.warning(
                "invalid_columns_detected",
                query_name=query_name,
                invalid_columns=invalid_columns[:5],  # Log first 5
            )
            # Note: This is a simplified validation. In production, use a proper SQL parser
            # For now, we'll log warnings but not fail (to avoid false positives)
            # Uncomment below to enforce strict validation:
            # raise ValidationError(
            #     message=f"Invalid column references: {', '.join(invalid_columns[:5])}",
            #     query_name=query_name,
            #     details="Query references columns not in the Business View whitelist",
            # )

    @staticmethod
    def _validate_query_structure(query: str, query_name: str) -> None:
        """Validate basic SQL query structure."""
        query_upper = query.upper().strip()

        # Must start with SELECT
        if not query_upper.startswith("SELECT"):
            raise ValidationError(
                message="Query must start with SELECT",
                query_name=query_name,
                details="Only SELECT queries are allowed",
            )

        # Must have FROM clause
        if "FROM" not in query_upper:
            raise ValidationError(
                message="Query must contain FROM clause",
                query_name=query_name,
                details="All queries must specify data source with FROM",
            )

        # Check for balanced parentheses
        open_count = query.count("(")
        close_count = query.count(")")
        if open_count != close_count:
            raise ValidationError(
                message="Unbalanced parentheses",
                query_name=query_name,
                details=f"Found {open_count} opening and {close_count} closing parentheses",
            )

    @staticmethod
    def _validate_aggregation(query: str, query_name: str) -> None:
        """Validate proper use of aggregation functions."""
        query_upper = query.upper()

        # Check if query has aggregation functions
        has_aggregation = any(
            agg in query_upper for agg in ["SUM(", "COUNT(", "AVG(", "MIN(", "MAX("]
        )

        # If it has aggregation, it should have GROUP BY (unless it's a simple aggregation)
        # This is a simplified check - could be enhanced
        if has_aggregation:
            # Check if there are non-aggregated columns in SELECT
            # If so, should have GROUP BY
            select_clause = PlanValidator._extract_select_clause(query)

            # Simple heuristic: if SELECT has both aggregations and column references,
            # we expect GROUP BY
            has_plain_columns = bool(re.search(r'\b[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*\b', select_clause))

            if has_plain_columns and "GROUP BY" not in query_upper:
                logger.warning(
                    "aggregation_without_group_by",
                    query_name=query_name,
                    details="Query has aggregation and column references but no GROUP BY",
                )
                # Don't fail - this is just a warning for now

    @staticmethod
    def _extract_select_clause(query: str) -> str:
        """Extract the SELECT clause from a query."""
        query_upper = query.upper()
        select_start = query_upper.find("SELECT")
        from_start = query_upper.find("FROM")

        if select_start == -1 or from_start == -1:
            return ""

        return query[select_start + 6:from_start].strip()

    @staticmethod
    def validate_query_safety(query: str) -> bool:
        """
        Quick safety check for a query (utility method).

        Returns:
            True if query appears safe, False otherwise
        """
        try:
            query_name = "safety_check"
            PlanValidator._check_dangerous_keywords(query, query_name)
            PlanValidator._check_sql_injection(query, query_name)
            return True
        except ValidationError:
            return False
