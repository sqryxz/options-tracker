#!/usr/bin/env python3

import unittest
import sys
from pathlib import Path

def run_tests():
    """Run all tests in the tests directory."""
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    
    # Add the src directory to the path
    sys.path.insert(0, str(script_dir / "src"))
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = script_dir / "tests"
    suite = loader.discover(start_dir)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests()) 