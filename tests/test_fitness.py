import pytest
from src.production_fitness import ProductionFitnessEvaluator, CodeSandbox
from src.utils import Solution, Task


def test_syntax_valid():
    """Test that valid Python code receives a high fitness score."""
    evaluator = ProductionFitnessEvaluator()
    solution = Solution(code='def foo():\n    return 1')
    task = Task()
    fitness = evaluator.evaluate(solution, task)
    assert fitness > 0.5


def test_syntax_invalid():
    """Test that code with syntax errors receives a low fitness score."""
    evaluator = ProductionFitnessEvaluator()
    solution = Solution(code='def foo(:\n    return 1')  # Missing closing parenthesis
    task = Task()
    fitness = evaluator.evaluate(solution, task)
    assert fitness < 0.5


def test_security_scan_dangerous():
    """Test that code containing dangerous operations receives very low fitness."""
    evaluator = ProductionFitnessEvaluator()
    solution = Solution(code='import os\nos.system("rm -rf /")')
    task = Task()
    fitness = evaluator.evaluate(solution, task)
    assert fitness < 0.3  # Security failure should drastically reduce fitness


def test_security_scan_safe():
    """Test that safe code receives higher fitness than dangerous code."""
    evaluator = ProductionFitnessEvaluator()
    solution = Solution(code='def safe_function():\n    x = 1 + 1\n    return x')
    task = Task()
    fitness = evaluator.evaluate(solution, task)
    assert fitness > 0.5


def test_sandbox_execution_success():
    """Test that executable code in sandbox returns non-zero fitness."""
    evaluator = ProductionFitnessEvaluator()
    solution = Solution(code='def add(a, b):\n    return a + b\n\nresult = add(2, 3)')
    task = Task()
    fitness = evaluator.evaluate(solution, task)
    assert fitness > 0.0


def test_composite_fitness_calculation():
    """Test that weighted scoring works correctly."""
    evaluator = ProductionFitnessEvaluator()
    # Test with valid, safe, executable code
    solution = Solution(code='def multiply(a, b):\n    return a * b\n\nresult = multiply(3, 4)')
    task = Task()
    fitness = evaluator.evaluate(solution, task)
    # With valid syntax, safe code, and successful execution, fitness should be high
    assert fitness > 0.6
    assert fitness <= 1.0
