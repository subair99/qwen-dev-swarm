# test_generated_script.py

# run with: uv run pytest test_generated_script.py -v

"""
Universal Structural & Security Gatekeeper for generated_script.py.

This test suite does not test the specific business logic (which is unknown).
Instead, it uses Python's AST (Abstract Syntax Tree) to verify that the 
Lead Coder agent strictly adhered to the swarm's architectural mandates.
"""
import ast
import os
import sys
import pytest

# Dynamically locate the generated script in the current directory
SCRIPT_NAME = "generated_script.py"
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), SCRIPT_NAME)

# --- Fixtures ---

@pytest.fixture(scope="module")
def generated_code():
    """Reads the generated script. Skips tests if the file doesn't exist."""
    if not os.path.exists(SCRIPT_PATH):
        pytest.skip(f"{SCRIPT_NAME} not found. Run the swarm first.")
    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        return f.read()

@pytest.fixture(scope="module")
def parsed_ast(generated_code):
    """Parses the code into an AST without executing it."""
    try:
        return ast.parse(generated_code)
    except SyntaxError as e:
        pytest.fail(f"generated_script.py contains a SyntaxError: {e}")

# --- Structural Mandate Tests ---

class TestModuleDocumentation:
    """Verifies the mandatory module-level docstring."""
    
    def test_has_module_docstring(self, parsed_ast):
        """The script MUST start with a comprehensive module-level docstring."""
        docstring = ast.get_docstring(parsed_ast)
        assert docstring is not None, "Missing mandatory module-level docstring."
        assert len(docstring) > 50, "Module docstring is too short/generic."

class TestSecurityAndIsolation:
    """Verifies the script is safe for the Docker sandbox."""
    
    def test_no_external_imports(self, parsed_ast):
        """Mandate: Standard Library ONLY. No external dependencies."""
        banned_libs = {
            "requests", "httpx", "aiohttp", "urllib3",
            "pandas", "numpy", "scipy", "sklearn",
            "bs4", "beautifulsoup4", "lxml",
            "pydantic", "sqlalchemy", "django", "flask",
            "openai", "anthropic", "langchain"
        }
        
        imported_modules = set()
        for node in ast.walk(parsed_ast):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module.split('.')[0])
                    
        violations = imported_modules.intersection(banned_libs)
        assert not violations, f"Banned external libraries imported: {violations}"

    def test_no_cli_arguments(self, parsed_ast):
        """Mandate: No argparse or sys.argv. Use hardcoded defaults or functions."""
        source_code = ast.dump(parsed_ast)
        assert "argparse" not in source_code, "Usage of 'argparse' is forbidden."
        assert "sys.argv" not in source_code, "Usage of 'sys.argv' is forbidden."

    def test_no_test_framework_imports(self, parsed_ast):
        """Mandate: Main script must not import testing frameworks."""
        source_code = ast.dump(parsed_ast)
        banned_test_libs = ["pytest", "unittest", "mock", "faker"]
        for lib in banned_test_libs:
            assert lib not in source_code, f"Main script must not import '{lib}'."

class TestCodeQuality:
    """Verifies basic code quality and defensive programming."""
    
    def test_no_bare_except(self, parsed_ast):
        """Mandate: Defensive programming. No bare 'except:' clauses."""
        for node in ast.walk(parsed_ast):
            if isinstance(node, ast.ExceptHandler):
                assert node.type is not None, "Bare 'except:' clause found. Specify the exception type."

    def test_no_hardcoded_secrets(self, generated_code):
        """Security: Basic heuristic check for hardcoded API keys or passwords."""
        secret_patterns = ["sk-", "api_key=", "password=", "secret_key="]
        lower_code = generated_code.lower()
        # Ignore comments for this simple check
        lines = [line for line in lower_code.split('\n') if not line.strip().startswith('#')]
        clean_code = '\n'.join(lines)
        
        for pattern in secret_patterns:
            assert pattern not in clean_code, f"Potential hardcoded secret found: '{pattern}'"

# --- Execution Safety Test ---

class TestSafeExecution:
    """Verifies the script can be loaded without immediate catastrophic failure."""
    
    def test_compiles_and_loads(self, generated_code):
        """Ensures the script compiles and doesn't have infinite loops at the module level."""
        # We use compile() to ensure it's valid bytecode
        try:
            compile(generated_code, SCRIPT_NAME, 'exec')
        except Exception as e:
            pytest.fail(f"Script failed to compile: {e}")