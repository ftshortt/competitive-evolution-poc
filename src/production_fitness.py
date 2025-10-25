import subprocess
import tempfile
import os
import ast
import re
from pathlib import Path
from typing import Dict, Any
from src.utils import Solution, Task


class CodeSandbox:
    """Executes code in a sandboxed environment with timeout protection."""
    
    def execute(self, code: str, timeout: int = 5) -> float:
        """
        Executes code in a temporary directory with subprocess and timeout protection.
        
        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds (default: 5)
            
        Returns:
            1.0 for successful execution, 0.0 for failure or timeout
        """
        try:
            # Create a temporary directory for execution
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write code to a temporary file
                temp_file = Path(temp_dir) / "temp_code.py"
                temp_file.write_text(code)
                
                # Execute the code with timeout protection
                result = subprocess.run(
                    ["python", str(temp_file)],
                    capture_output=True,
                    timeout=timeout,
                    cwd=temp_dir
                )
                
                # Return 1.0 for success (exit code 0), 0.0 for failure
                return 1.0 if result.returncode == 0 else 0.0
                
        except subprocess.TimeoutExpired:
            # Timeout occurred
            return 0.0
        except Exception:
            # Any other exception
            return 0.0


class ProductionFitnessEvaluator:
    """Evaluates code quality with comprehensive fitness metrics."""
    
    def __init__(self):
        self.sandbox = CodeSandbox()
    
    def check_syntax(self, code: str) -> float:
        """
        Checks if the code has valid Python syntax.
        
        Args:
            code: Python code to check
            
        Returns:
            1.0 for valid syntax, 0.0 for syntax errors
        """
        try:
            ast.parse(code)
            return 1.0
        except SyntaxError:
            return 0.0
    
    def security_scan(self, code: str) -> float:
        """
        Scans code for dangerous operations.
        
        Args:
            code: Python code to scan
            
        Returns:
            1.0 if no dangerous operations found, 0.0 otherwise
        """
        dangerous_operations = [
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'\bos\.system\s*\(',
            r'\bsubprocess\.',
        ]
        
        for pattern in dangerous_operations:
            if re.search(pattern, code):
                return 0.0
        
        return 1.0
    
    def run_tests(self, code: str, task: Task) -> float:
        """
        Placeholder for test suite execution.
        
        Args:
            code: Python code to test
            task: Task containing test specifications
            
        Returns:
            Test success rate (0.0 to 1.0)
        """
        # Placeholder implementation
        # In production, this would run actual test suites
        return 0.5
    
    def evaluate(self, solution: Solution, task: Task) -> float:
        """
        Computes composite fitness score from multiple metrics.
        
        Weights:
        - Syntax: 0.2
        - Execution: 0.3
        - Security: 0.2
        - Reasoning depth: 0.2 (based on reasoning_steps/15)
        - Efficiency: 0.1 (based on token_cost/3000)
        
        Args:
            solution: Solution object containing code and metadata
            task: Task object with problem specification
            
        Returns:
            Composite fitness score (0.0 to 1.0)
        """
        # Syntax check (weight: 0.2)
        syntax_score = self.check_syntax(solution.code)
        
        # Execution check (weight: 0.3)
        execution_score = self.sandbox.execute(solution.code)
        
        # Security scan (weight: 0.2)
        security_score = self.security_scan(solution.code)
        
        # Reasoning depth (weight: 0.2, based on reasoning_steps/15)
        reasoning_steps = getattr(solution, 'reasoning_steps', 0)
        reasoning_score = min(reasoning_steps / 15.0, 1.0)
        
        # Efficiency (weight: 0.1, based on token_cost/3000)
        token_cost = getattr(solution, 'token_cost', 3000)
        efficiency_score = max(1.0 - (token_cost / 3000.0), 0.0)
        
        # Compute weighted composite score
        composite_score = (
            syntax_score * 0.2 +
            execution_score * 0.3 +
            security_score * 0.2 +
            reasoning_score * 0.2 +
            efficiency_score * 0.1
        )
        
        return composite_score
