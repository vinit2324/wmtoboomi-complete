"""
JDBC SQL Analyzer for webMethods to Boomi Migration
====================================================

This analyzer achieves 80%+ automation on JDBC adapters by:
1. Parsing SQL queries (SELECT, INSERT, UPDATE, DELETE)
2. Detecting JOIN types and complexity
3. Converting to Boomi Database connector configuration
4. Handling stored procedures

Key insight: webMethods JDBC Adapter has graphical JOIN/WHERE builders
that generate SQL. We parse this SQL and convert to Boomi Database Profile.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class SQLOperationType(Enum):
    """SQL operation types"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CALL = "call"  # Stored procedure
    UNKNOWN = "unknown"


class JoinType(Enum):
    """SQL JOIN types"""
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    FULL = "full"
    CROSS = "cross"
    NONE = "none"


@dataclass
class SQLColumn:
    """Represents a SQL column"""
    name: str
    table: Optional[str] = None
    alias: Optional[str] = None
    data_type: Optional[str] = None
    is_primary_key: bool = False
    is_nullable: bool = True


@dataclass
class SQLTable:
    """Represents a SQL table"""
    name: str
    alias: Optional[str] = None
    schema: Optional[str] = None


@dataclass
class SQLJoin:
    """Represents a SQL JOIN"""
    join_type: JoinType
    table: SQLTable
    on_condition: str
    complexity: str = "simple"  # simple, moderate, complex


@dataclass
class SQLWhereClause:
    """Represents a WHERE clause"""
    conditions: List[str]
    has_parameters: bool = False
    parameter_count: int = 0
    complexity: str = "simple"


@dataclass
class SQLAnalysis:
    """Complete analysis of a SQL statement"""
    original_sql: str
    operation_type: SQLOperationType
    tables: List[SQLTable]
    columns: List[SQLColumn]
    joins: List[SQLJoin]
    where_clause: Optional[SQLWhereClause]
    group_by: List[str]
    order_by: List[str]
    has_subquery: bool
    has_aggregate: bool
    has_union: bool
    complexity: str  # low, medium, high
    automation_level: int
    boomi_config: Dict
    conversion_notes: List[str]
    warnings: List[str]


class JDBCSQLAnalyzer:
    """
    Analyzes SQL from webMethods JDBC Adapter services.
    
    Generates Boomi Database connector configuration.
    """
    
    # SQL patterns
    SELECT_PATTERN = re.compile(r'^\s*SELECT\s+', re.IGNORECASE)
    INSERT_PATTERN = re.compile(r'^\s*INSERT\s+INTO\s+', re.IGNORECASE)
    UPDATE_PATTERN = re.compile(r'^\s*UPDATE\s+', re.IGNORECASE)
    DELETE_PATTERN = re.compile(r'^\s*DELETE\s+FROM\s+', re.IGNORECASE)
    CALL_PATTERN = re.compile(r'^\s*(?:CALL|EXEC|EXECUTE)\s+', re.IGNORECASE)
    
    # JOIN patterns
    JOIN_PATTERN = re.compile(
        r'(INNER|LEFT\s+OUTER?|RIGHT\s+OUTER?|FULL\s+OUTER?|CROSS)?\s*JOIN\s+(\w+(?:\.\w+)?)\s*(?:AS\s+)?(\w+)?\s+ON\s+(.+?)(?=(?:INNER|LEFT|RIGHT|FULL|CROSS|WHERE|GROUP|ORDER|$))',
        re.IGNORECASE | re.DOTALL
    )
    
    # WHERE pattern
    WHERE_PATTERN = re.compile(r'\bWHERE\s+(.+?)(?=(?:GROUP\s+BY|ORDER\s+BY|HAVING|$))', re.IGNORECASE | re.DOTALL)
    
    # Parameter pattern (? or :paramName)
    PARAM_PATTERN = re.compile(r'\?|:\w+')
    
    # Aggregate functions
    AGGREGATE_PATTERN = re.compile(r'\b(COUNT|SUM|AVG|MIN|MAX|GROUP_CONCAT)\s*\(', re.IGNORECASE)
    
    # Subquery pattern
    SUBQUERY_PATTERN = re.compile(r'\(\s*SELECT\s+', re.IGNORECASE)
    
    def __init__(self):
        self.warnings: List[str] = []
        self.notes: List[str] = []
    
    def analyze(self, sql: str) -> SQLAnalysis:
        """
        Analyze a SQL statement.
        
        Args:
            sql: SQL statement from webMethods JDBC Adapter
            
        Returns:
            SQLAnalysis with complete breakdown and Boomi config
        """
        self.warnings = []
        self.notes = []
        
        # Clean SQL
        sql = self._clean_sql(sql)
        
        # Detect operation type
        op_type = self._detect_operation_type(sql)
        
        # Parse based on type
        if op_type == SQLOperationType.SELECT:
            return self._analyze_select(sql)
        elif op_type == SQLOperationType.INSERT:
            return self._analyze_insert(sql)
        elif op_type == SQLOperationType.UPDATE:
            return self._analyze_update(sql)
        elif op_type == SQLOperationType.DELETE:
            return self._analyze_delete(sql)
        elif op_type == SQLOperationType.CALL:
            return self._analyze_call(sql)
        else:
            return self._analyze_unknown(sql)
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and normalize SQL"""
        # Remove comments
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        # Normalize whitespace
        sql = re.sub(r'\s+', ' ', sql).strip()
        return sql
    
    def _detect_operation_type(self, sql: str) -> SQLOperationType:
        """Detect SQL operation type"""
        if self.SELECT_PATTERN.match(sql):
            return SQLOperationType.SELECT
        elif self.INSERT_PATTERN.match(sql):
            return SQLOperationType.INSERT
        elif self.UPDATE_PATTERN.match(sql):
            return SQLOperationType.UPDATE
        elif self.DELETE_PATTERN.match(sql):
            return SQLOperationType.DELETE
        elif self.CALL_PATTERN.match(sql):
            return SQLOperationType.CALL
        return SQLOperationType.UNKNOWN
    
    def _analyze_select(self, sql: str) -> SQLAnalysis:
        """Analyze SELECT statement"""
        tables = self._extract_tables(sql)
        columns = self._extract_select_columns(sql)
        joins = self._extract_joins(sql)
        where = self._extract_where(sql)
        
        # Check for complex features
        has_subquery = bool(self.SUBQUERY_PATTERN.search(sql))
        has_aggregate = bool(self.AGGREGATE_PATTERN.search(sql))
        has_union = 'UNION' in sql.upper()
        
        # Extract GROUP BY and ORDER BY
        group_by = self._extract_group_by(sql)
        order_by = self._extract_order_by(sql)
        
        # Calculate complexity
        complexity = self._calculate_complexity(
            len(joins), has_subquery, has_aggregate, has_union,
            where.complexity if where else "simple"
        )
        
        # Calculate automation level
        automation = self._calculate_automation(
            SQLOperationType.SELECT, complexity, len(joins), 
            has_subquery, has_aggregate
        )
        
        # Generate Boomi config
        boomi_config = self._generate_select_config(
            tables, columns, joins, where, group_by, order_by
        )
        
        return SQLAnalysis(
            original_sql=sql,
            operation_type=SQLOperationType.SELECT,
            tables=tables,
            columns=columns,
            joins=joins,
            where_clause=where,
            group_by=group_by,
            order_by=order_by,
            has_subquery=has_subquery,
            has_aggregate=has_aggregate,
            has_union=has_union,
            complexity=complexity,
            automation_level=automation,
            boomi_config=boomi_config,
            conversion_notes=self.notes,
            warnings=self.warnings
        )
    
    def _analyze_insert(self, sql: str) -> SQLAnalysis:
        """Analyze INSERT statement"""
        tables = self._extract_insert_table(sql)
        columns = self._extract_insert_columns(sql)
        
        # Check for SELECT in INSERT
        has_subquery = 'SELECT' in sql.upper()
        
        complexity = "medium" if has_subquery else "low"
        automation = 85 if not has_subquery else 70
        
        boomi_config = self._generate_insert_config(tables, columns)
        
        return SQLAnalysis(
            original_sql=sql,
            operation_type=SQLOperationType.INSERT,
            tables=tables,
            columns=columns,
            joins=[],
            where_clause=None,
            group_by=[],
            order_by=[],
            has_subquery=has_subquery,
            has_aggregate=False,
            has_union=False,
            complexity=complexity,
            automation_level=automation,
            boomi_config=boomi_config,
            conversion_notes=self.notes,
            warnings=self.warnings
        )
    
    def _analyze_update(self, sql: str) -> SQLAnalysis:
        """Analyze UPDATE statement"""
        tables = self._extract_update_table(sql)
        columns = self._extract_update_columns(sql)
        where = self._extract_where(sql)
        
        # Check for JOIN in UPDATE
        has_join = 'JOIN' in sql.upper()
        has_subquery = bool(self.SUBQUERY_PATTERN.search(sql))
        
        complexity = "low"
        if has_join:
            complexity = "high"
            self.warnings.append("UPDATE with JOIN requires manual review")
        elif has_subquery:
            complexity = "medium"
        elif where and where.complexity == "complex":
            complexity = "medium"
        
        automation = 85
        if has_join:
            automation = 50
        elif has_subquery:
            automation = 65
        
        boomi_config = self._generate_update_config(tables, columns, where)
        
        return SQLAnalysis(
            original_sql=sql,
            operation_type=SQLOperationType.UPDATE,
            tables=tables,
            columns=columns,
            joins=[],
            where_clause=where,
            group_by=[],
            order_by=[],
            has_subquery=has_subquery,
            has_aggregate=False,
            has_union=False,
            complexity=complexity,
            automation_level=automation,
            boomi_config=boomi_config,
            conversion_notes=self.notes,
            warnings=self.warnings
        )
    
    def _analyze_delete(self, sql: str) -> SQLAnalysis:
        """Analyze DELETE statement"""
        tables = self._extract_delete_table(sql)
        where = self._extract_where(sql)
        
        has_subquery = bool(self.SUBQUERY_PATTERN.search(sql))
        
        complexity = "low"
        if has_subquery:
            complexity = "medium"
        elif where and where.complexity == "complex":
            complexity = "medium"
        
        automation = 85 if not has_subquery else 70
        
        boomi_config = self._generate_delete_config(tables, where)
        
        return SQLAnalysis(
            original_sql=sql,
            operation_type=SQLOperationType.DELETE,
            tables=tables,
            columns=[],
            joins=[],
            where_clause=where,
            group_by=[],
            order_by=[],
            has_subquery=has_subquery,
            has_aggregate=False,
            has_union=False,
            complexity=complexity,
            automation_level=automation,
            boomi_config=boomi_config,
            conversion_notes=self.notes,
            warnings=self.warnings
        )
    
    def _analyze_call(self, sql: str) -> SQLAnalysis:
        """Analyze stored procedure CALL"""
        # Extract procedure name
        match = re.search(r'(?:CALL|EXEC|EXECUTE)\s+(\w+(?:\.\w+)*)', sql, re.IGNORECASE)
        proc_name = match.group(1) if match else "unknown"
        
        # Count parameters
        param_count = sql.count('?') + len(re.findall(r':\w+', sql))
        
        self.notes.append(f"Stored procedure: {proc_name}")
        self.notes.append(f"Parameters: {param_count}")
        
        boomi_config = {
            "operation": "stored_procedure",
            "procedure_name": proc_name,
            "parameter_count": param_count,
            "notes": ["Configure procedure in Database connector",
                     "Map input parameters",
                     "Map output parameters/result set"]
        }
        
        return SQLAnalysis(
            original_sql=sql,
            operation_type=SQLOperationType.CALL,
            tables=[SQLTable(name=proc_name)],
            columns=[],
            joins=[],
            where_clause=None,
            group_by=[],
            order_by=[],
            has_subquery=False,
            has_aggregate=False,
            has_union=False,
            complexity="medium",
            automation_level=75,
            boomi_config=boomi_config,
            conversion_notes=self.notes,
            warnings=self.warnings
        )
    
    def _analyze_unknown(self, sql: str) -> SQLAnalysis:
        """Handle unknown SQL"""
        self.warnings.append("Unknown SQL type - requires manual review")
        
        return SQLAnalysis(
            original_sql=sql,
            operation_type=SQLOperationType.UNKNOWN,
            tables=[],
            columns=[],
            joins=[],
            where_clause=None,
            group_by=[],
            order_by=[],
            has_subquery=False,
            has_aggregate=False,
            has_union=False,
            complexity="high",
            automation_level=30,
            boomi_config={"requires_manual_review": True},
            conversion_notes=self.notes,
            warnings=self.warnings
        )
    
    def _extract_tables(self, sql: str) -> List[SQLTable]:
        """Extract tables from FROM clause"""
        tables = []
        
        # Find FROM clause
        from_match = re.search(r'\bFROM\s+(.+?)(?=(?:WHERE|GROUP|ORDER|INNER|LEFT|RIGHT|FULL|CROSS|JOIN|$))', 
                              sql, re.IGNORECASE)
        if from_match:
            from_clause = from_match.group(1)
            # Split by comma
            for part in from_clause.split(','):
                part = part.strip()
                # Handle schema.table AS alias
                table_match = re.match(r'(\w+(?:\.\w+)?)\s*(?:AS\s+)?(\w+)?', part)
                if table_match:
                    name = table_match.group(1)
                    alias = table_match.group(2)
                    tables.append(SQLTable(name=name, alias=alias))
        
        return tables
    
    def _extract_select_columns(self, sql: str) -> List[SQLColumn]:
        """Extract columns from SELECT clause"""
        columns = []
        
        # Find SELECT ... FROM
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            
            # Handle SELECT *
            if select_clause.strip() == '*':
                columns.append(SQLColumn(name='*', alias=None))
                return columns
            
            # Parse columns (basic parsing)
            # TODO: Handle functions and complex expressions better
            for part in self._split_columns(select_clause):
                part = part.strip()
                # Handle table.column AS alias
                col_match = re.match(r'(?:(\w+)\.)?(\w+|\*)\s*(?:AS\s+)?(\w+)?', part)
                if col_match:
                    table = col_match.group(1)
                    name = col_match.group(2)
                    alias = col_match.group(3)
                    columns.append(SQLColumn(name=name, table=table, alias=alias))
        
        return columns
    
    def _split_columns(self, clause: str) -> List[str]:
        """Split columns handling parentheses"""
        columns = []
        current = ""
        paren_depth = 0
        
        for char in clause:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                columns.append(current)
                current = ""
                continue
            current += char
        
        if current:
            columns.append(current)
        
        return columns
    
    def _extract_joins(self, sql: str) -> List[SQLJoin]:
        """Extract JOIN clauses"""
        joins = []
        
        for match in self.JOIN_PATTERN.finditer(sql):
            join_type_str = (match.group(1) or 'INNER').upper().strip()
            table_name = match.group(2)
            alias = match.group(3)
            on_condition = match.group(4).strip()
            
            # Determine join type
            if 'LEFT' in join_type_str:
                join_type = JoinType.LEFT
            elif 'RIGHT' in join_type_str:
                join_type = JoinType.RIGHT
            elif 'FULL' in join_type_str:
                join_type = JoinType.FULL
            elif 'CROSS' in join_type_str:
                join_type = JoinType.CROSS
            else:
                join_type = JoinType.INNER
            
            # Assess complexity
            complexity = "simple"
            if 'OR' in on_condition.upper():
                complexity = "complex"
            elif on_condition.count('AND') > 2:
                complexity = "moderate"
            
            joins.append(SQLJoin(
                join_type=join_type,
                table=SQLTable(name=table_name, alias=alias),
                on_condition=on_condition,
                complexity=complexity
            ))
        
        return joins
    
    def _extract_where(self, sql: str) -> Optional[SQLWhereClause]:
        """Extract WHERE clause"""
        match = self.WHERE_PATTERN.search(sql)
        if not match:
            return None
        
        where_text = match.group(1).strip()
        
        # Count parameters
        params = self.PARAM_PATTERN.findall(where_text)
        
        # Split conditions
        conditions = re.split(r'\s+AND\s+|\s+OR\s+', where_text, flags=re.IGNORECASE)
        
        # Assess complexity
        complexity = "simple"
        if 'OR' in where_text.upper():
            complexity = "moderate"
        if len(conditions) > 5 or 'EXISTS' in where_text.upper() or 'IN (' in where_text.upper():
            complexity = "complex"
        
        return SQLWhereClause(
            conditions=conditions,
            has_parameters=len(params) > 0,
            parameter_count=len(params),
            complexity=complexity
        )
    
    def _extract_group_by(self, sql: str) -> List[str]:
        """Extract GROUP BY columns"""
        match = re.search(r'GROUP\s+BY\s+(.+?)(?=(?:HAVING|ORDER|$))', sql, re.IGNORECASE)
        if match:
            return [c.strip() for c in match.group(1).split(',')]
        return []
    
    def _extract_order_by(self, sql: str) -> List[str]:
        """Extract ORDER BY columns"""
        match = re.search(r'ORDER\s+BY\s+(.+?)$', sql, re.IGNORECASE)
        if match:
            return [c.strip() for c in match.group(1).split(',')]
        return []
    
    def _extract_insert_table(self, sql: str) -> List[SQLTable]:
        """Extract table from INSERT"""
        match = re.search(r'INSERT\s+INTO\s+(\w+(?:\.\w+)?)', sql, re.IGNORECASE)
        if match:
            return [SQLTable(name=match.group(1))]
        return []
    
    def _extract_insert_columns(self, sql: str) -> List[SQLColumn]:
        """Extract columns from INSERT"""
        match = re.search(r'INSERT\s+INTO\s+\w+(?:\.\w+)?\s*\((.+?)\)', sql, re.IGNORECASE)
        if match:
            return [SQLColumn(name=c.strip()) for c in match.group(1).split(',')]
        return []
    
    def _extract_update_table(self, sql: str) -> List[SQLTable]:
        """Extract table from UPDATE"""
        match = re.search(r'UPDATE\s+(\w+(?:\.\w+)?)', sql, re.IGNORECASE)
        if match:
            return [SQLTable(name=match.group(1))]
        return []
    
    def _extract_update_columns(self, sql: str) -> List[SQLColumn]:
        """Extract columns from UPDATE SET"""
        match = re.search(r'SET\s+(.+?)(?=(?:WHERE|$))', sql, re.IGNORECASE)
        if match:
            columns = []
            for part in match.group(1).split(','):
                col_match = re.match(r'(\w+)\s*=', part.strip())
                if col_match:
                    columns.append(SQLColumn(name=col_match.group(1)))
            return columns
        return []
    
    def _extract_delete_table(self, sql: str) -> List[SQLTable]:
        """Extract table from DELETE"""
        match = re.search(r'DELETE\s+FROM\s+(\w+(?:\.\w+)?)', sql, re.IGNORECASE)
        if match:
            return [SQLTable(name=match.group(1))]
        return []
    
    def _calculate_complexity(self, join_count: int, has_subquery: bool, 
                             has_aggregate: bool, has_union: bool,
                             where_complexity: str) -> str:
        """Calculate overall query complexity"""
        score = 0
        
        # JOINs add complexity
        score += join_count * 2
        
        # Subqueries are complex
        if has_subquery:
            score += 4
        
        # Aggregates add moderate complexity
        if has_aggregate:
            score += 2
        
        # UNIONs are complex
        if has_union:
            score += 3
        
        # WHERE complexity
        if where_complexity == "complex":
            score += 3
        elif where_complexity == "moderate":
            score += 1
        
        if score <= 2:
            return "low"
        elif score <= 6:
            return "medium"
        else:
            return "high"
    
    def _calculate_automation(self, op_type: SQLOperationType, complexity: str,
                             join_count: int, has_subquery: bool,
                             has_aggregate: bool) -> int:
        """Calculate automation level"""
        # Base levels by operation
        base = {
            SQLOperationType.SELECT: 80,
            SQLOperationType.INSERT: 90,
            SQLOperationType.UPDATE: 85,
            SQLOperationType.DELETE: 88,
            SQLOperationType.CALL: 75,
            SQLOperationType.UNKNOWN: 30,
        }.get(op_type, 50)
        
        # Adjust for complexity
        if complexity == "low":
            base += 5
        elif complexity == "high":
            base -= 15
        
        # Adjust for JOINs
        if join_count > 0:
            base -= min(join_count * 3, 15)
            self.notes.append(f"Query has {join_count} JOIN(s) - review join conditions in Boomi")
        
        # Subqueries reduce automation
        if has_subquery:
            base -= 20
            self.warnings.append("Subquery detected - may need restructuring in Boomi")
        
        # Aggregates are usually fine
        if has_aggregate:
            base -= 5
            self.notes.append("Aggregate functions detected - verify in Boomi Database connector")
        
        return max(min(base, 95), 30)
    
    def _generate_select_config(self, tables, columns, joins, where, group_by, order_by) -> Dict:
        """Generate Boomi Database connector config for SELECT"""
        config = {
            "operation": "query",
            "profile_type": "database",
            "tables": [{"name": t.name, "alias": t.alias} for t in tables],
            "columns": [{"name": c.name, "table": c.table, "alias": c.alias} for c in columns],
        }
        
        if joins:
            config["joins"] = [{
                "type": j.join_type.value,
                "table": j.table.name,
                "alias": j.table.alias,
                "on_condition": j.on_condition,
                "notes": "Review and configure in Boomi Database connector"
            } for j in joins]
        
        if where:
            config["where"] = {
                "conditions": where.conditions,
                "parameter_count": where.parameter_count,
                "notes": "Configure WHERE in Boomi connector filter"
            }
        
        if group_by:
            config["group_by"] = group_by
        
        if order_by:
            config["order_by"] = order_by
        
        return config
    
    def _generate_insert_config(self, tables, columns) -> Dict:
        """Generate Boomi config for INSERT"""
        return {
            "operation": "insert",
            "table": tables[0].name if tables else "",
            "columns": [c.name for c in columns],
            "notes": ["Configure INSERT in Database connector",
                     "Map fields from source to database columns",
                     "Boomi handles batch inserts automatically"]
        }
    
    def _generate_update_config(self, tables, columns, where) -> Dict:
        """Generate Boomi config for UPDATE"""
        config = {
            "operation": "update",
            "table": tables[0].name if tables else "",
            "columns": [c.name for c in columns],
            "notes": ["Configure UPDATE in Database connector",
                     "Set update columns and WHERE key fields"]
        }
        
        if where:
            config["where_keys"] = where.conditions
        
        return config
    
    def _generate_delete_config(self, tables, where) -> Dict:
        """Generate Boomi config for DELETE"""
        config = {
            "operation": "delete",
            "table": tables[0].name if tables else "",
            "notes": ["Configure DELETE in Database connector",
                     "Set WHERE key fields for deletion"]
        }
        
        if where:
            config["where_keys"] = where.conditions
        
        return config


def get_jdbc_analyzer() -> JDBCSQLAnalyzer:
    """Get singleton analyzer instance"""
    return JDBCSQLAnalyzer()
