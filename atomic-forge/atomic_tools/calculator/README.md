# Calculator Tool

## Overview
The Calculator Tool is a Python-based utility designed for performing a variety of mathematical calculations. It supports basic arithmetic operations such as addition, subtraction, multiplication, and division, as well as more complex operations including exponentiation and trigonometric functions. This tool is built using the Pydantic library for input validation and the SymPy library for expression evaluation.

## Features
- Evaluate mathematical expressions.
- Support for basic and complex arithmetic operations.
- Input validation using Pydantic.
- User-friendly output formatting with Rich.

## Example Usage

```python
from calculator_tool import CalculatorTool

calculator = CalculatorTool()
result = calculator.run(expression="sin(pi/2) + cos(pi/4)")
print(result)  # Output: 1.853981633974483
```
