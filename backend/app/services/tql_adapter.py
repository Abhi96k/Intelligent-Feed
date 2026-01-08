"""TQL Adapter - Executes SQL queries against SQLite database."""

import sqlite3
from typing import Dict, Optional, Any
from pathlib import Path
import pandas as pd
from contextlib import contextmanager

from app.models.plan import TQLPlan
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class QueryExecutionError(Exception):
    """Raised when query execution fails."""

    def __init__(self, message: str, query_name: str = None, original_error: Exception = None):
        self.message = message
        self.query_name = query_name
        self.original_error = original_error
        super().__init__(self.message)


class QueryResults:
    """Container for query execution results."""

    def __init__(self):
        self.current_period: Optional[pd.DataFrame] = None
        self.baseline_period: Optional[pd.DataFrame] = None
        self.timeseries: Optional[pd.DataFrame] = None
        self.dimensional_breakdown: Optional[pd.DataFrame] = None
        self.baseline_dimensional_breakdown: Optional[pd.DataFrame] = None

    def has_baseline(self) -> bool:
        """Check if baseline results are available."""
        return self.baseline_period is not None

    def has_timeseries(self) -> bool:
        """Check if time-series results are available."""
        return self.timeseries is not None

    def has_dimensional_breakdown(self) -> bool:
        """Check if dimensional breakdown results are available."""
        return self.dimensional_breakdown is not None

    def get_current_value(self) -> Optional[float]:
        """Get scalar value from current period query."""
        if self.current_period is None or self.current_period.empty:
            return None
        # Assume single row, single column (metric_value)
        value = self.current_period.iloc[0]['metric_value']
        if value is None or (hasattr(value, '__class__') and str(value) == 'nan'):
            return None
        return float(value)

    def get_baseline_value(self) -> Optional[float]:
        """Get scalar value from baseline period query."""
        if self.baseline_period is None or self.baseline_period.empty:
            return None
        value = self.baseline_period.iloc[0]['metric_value']
        if value is None or (hasattr(value, '__class__') and str(value) == 'nan'):
            return None
        return float(value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary for logging/debugging."""
        return {
            "current_value": self.get_current_value(),
            "baseline_value": self.get_baseline_value(),
            "timeseries_rows": len(self.timeseries) if self.timeseries is not None else 0,
            "dimensional_breakdown_rows": len(self.dimensional_breakdown) if self.dimensional_breakdown is not None else 0,
        }


class TQLAdapter:
    """
    Adapter for executing TQL queries against SQLite database.

    This simulates the Tellius TQL service using SQLite as a backend.
    In production, this would connect to the actual Tellius TQL service.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize TQL adapter.

        Args:
            database_url: SQLite database URL (defaults to settings.DATABASE_URL)
        """
        self.database_url = database_url or settings.DATABASE_URL

        # Extract file path from database URL
        # Format: sqlite:///./path/to/db.db or sqlite:///path/to/db.db
        if self.database_url.startswith("sqlite:///"):
            self.db_path = self.database_url.replace("sqlite:///", "")
        else:
            raise ValueError(f"Unsupported database URL format: {self.database_url}")

        logger.info("tql_adapter_initialized", db_path=self.db_path)

    @contextmanager
    def _get_connection(self):
        """
        Get database connection context manager.

        Yields:
            sqlite3.Connection
        """
        conn = None
        try:
            # Create database file if it doesn't exist
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)

            # Connect with timeout
            conn = sqlite3.connect(
                self.db_path,
                timeout=settings.QUERY_TIMEOUT,
                check_same_thread=False,
            )

            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")

            # Set row factory to return dict-like rows
            conn.row_factory = sqlite3.Row

            yield conn

        except sqlite3.Error as e:
            logger.error("database_connection_error", error=str(e))
            raise QueryExecutionError(
                message="Failed to connect to database",
                original_error=e,
            )
        finally:
            if conn:
                conn.close()

    def execute(self, plan: TQLPlan) -> QueryResults:
        """
        Execute all queries in the TQL plan.

        Args:
            plan: TQL plan with queries to execute

        Returns:
            QueryResults with all executed query results

        Raises:
            QueryExecutionError: If query execution fails
        """
        logger.info(
            "executing_tql_plan",
            queries_count=len(plan.get_all_queries()),
            has_baseline=plan.requires_baseline(),
            has_timeseries=plan.requires_timeseries(),
        )

        results = QueryResults()

        with self._get_connection() as conn:
            # Execute current period query
            results.current_period = self._execute_query(
                conn, plan.current_period_query, "current_period"
            )

            # Execute baseline period query (if present)
            if plan.baseline_period_query:
                results.baseline_period = self._execute_query(
                    conn, plan.baseline_period_query, "baseline_period"
                )

            # Execute time-series query (if present)
            if plan.timeseries_query:
                results.timeseries = self._execute_query(
                    conn, plan.timeseries_query, "timeseries"
                )

            # Execute dimensional breakdown query (if present)
            if plan.dimensional_breakdown_query:
                results.dimensional_breakdown = self._execute_query(
                    conn, plan.dimensional_breakdown_query, "dimensional_breakdown"
                )

            # Execute baseline dimensional breakdown query (if present)
            if plan.baseline_dimensional_breakdown_query:
                results.baseline_dimensional_breakdown = self._execute_query(
                    conn, plan.baseline_dimensional_breakdown_query, "baseline_dimensional_breakdown"
                )

        logger.info(
            "tql_plan_executed_successfully",
            current_value=results.get_current_value(),
            baseline_value=results.get_baseline_value(),
        )

        return results

    def _execute_query(
        self, conn: sqlite3.Connection, query: str, query_name: str
    ) -> pd.DataFrame:
        """
        Execute a single SQL query and return results as DataFrame.

        Args:
            conn: Database connection
            query: SQL query to execute
            query_name: Name of the query (for logging)

        Returns:
            pandas DataFrame with query results

        Raises:
            QueryExecutionError: If query execution fails
        """
        logger.debug("executing_query", query_name=query_name, query=query[:200])

        try:
            # Execute query with pandas for easier DataFrame conversion
            df = pd.read_sql_query(query, conn)

            logger.info(
                "query_executed_successfully",
                query_name=query_name,
                rows_returned=len(df),
                columns=list(df.columns),
            )

            # Check row limit
            if len(df) > settings.MAX_QUERY_ROWS:
                logger.warning(
                    "query_exceeds_row_limit",
                    query_name=query_name,
                    rows=len(df),
                    limit=settings.MAX_QUERY_ROWS,
                )
                # Truncate to limit
                df = df.head(settings.MAX_QUERY_ROWS)

            return df

        except sqlite3.Error as e:
            logger.error(
                "query_execution_failed",
                query_name=query_name,
                error=str(e),
                query=query[:500],  # Log partial query for debugging
            )
            raise QueryExecutionError(
                message=f"Query execution failed: {str(e)}",
                query_name=query_name,
                original_error=e,
            )

        except pd.errors.DatabaseError as e:
            logger.error(
                "pandas_query_error",
                query_name=query_name,
                error=str(e),
            )
            raise QueryExecutionError(
                message=f"Pandas query error: {str(e)}",
                query_name=query_name,
                original_error=e,
            )

        except Exception as e:
            logger.error(
                "unexpected_query_error",
                query_name=query_name,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise QueryExecutionError(
                message=f"Unexpected error during query execution: {str(e)}",
                query_name=query_name,
                original_error=e,
            )

    def execute_raw_query(self, query: str) -> pd.DataFrame:
        """
        Execute a raw SQL query (utility method for testing).

        Args:
            query: Raw SQL query

        Returns:
            pandas DataFrame with results

        Raises:
            QueryExecutionError: If query execution fails
        """
        with self._get_connection() as conn:
            return self._execute_query(conn, query, "raw_query")

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error("connection_test_failed", error=str(e))
            return False

    def get_table_info(self, table_name: str) -> Optional[pd.DataFrame]:
        """
        Get information about a table's schema.

        Args:
            table_name: Name of the table

        Returns:
            DataFrame with table schema information, or None if table doesn't exist
        """
        try:
            query = f"PRAGMA table_info({table_name})"
            return self.execute_raw_query(query)
        except QueryExecutionError:
            return None

    def list_tables(self) -> list[str]:
        """
        List all tables in the database.

        Returns:
            List of table names
        """
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            df = self.execute_raw_query(query)
            return df['name'].tolist()
        except QueryExecutionError:
            return []

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table

        Returns:
            True if table exists, False otherwise
        """
        tables = self.list_tables()
        return table_name in tables

    def get_row_count(self, table_name: str) -> Optional[int]:
        """
        Get row count for a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows, or None if table doesn't exist
        """
        if not self.table_exists(table_name):
            return None

        try:
            query = f"SELECT COUNT(*) as count FROM {table_name}"
            df = self.execute_raw_query(query)
            return int(df.iloc[0]['count'])
        except QueryExecutionError:
            return None

    def initialize_database(self, schema_sql: Optional[str] = None) -> None:
        """
        Initialize database with schema and sample data.

        Args:
            schema_sql: Optional SQL script to initialize schema
        """
        if schema_sql:
            with self._get_connection() as conn:
                try:
                    conn.executescript(schema_sql)
                    conn.commit()
                    logger.info("database_initialized_successfully")
                except sqlite3.Error as e:
                    logger.error("database_initialization_failed", error=str(e))
                    raise QueryExecutionError(
                        message=f"Failed to initialize database: {str(e)}",
                        original_error=e,
                    )

    def execute_script(self, sql_script: str) -> None:
        """
        Execute a SQL script (multiple statements).

        Args:
            sql_script: SQL script with multiple statements

        Raises:
            QueryExecutionError: If script execution fails
        """
        with self._get_connection() as conn:
            try:
                conn.executescript(sql_script)
                conn.commit()
                logger.info("sql_script_executed_successfully")
            except sqlite3.Error as e:
                logger.error("sql_script_execution_failed", error=str(e))
                raise QueryExecutionError(
                    message=f"Failed to execute SQL script: {str(e)}",
                    original_error=e,
                )

    def close(self):
        """Close the adapter (no-op for SQLite with context manager)."""
        logger.info("tql_adapter_closed")
        pass
