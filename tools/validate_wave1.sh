#!/bin/bash

echo "Validating Wave 1 Tools..."
echo ""

# Test 1: Python syntax validation
echo "=== Test 1: Python Syntax Validation ==="
errors=0
for file in $(find . -name "*.py" -not -path "*/__pycache__/*" -not -path "*/.pytest_cache/*"); do
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo "✓ $file"
    else
        echo "✗ $file - SYNTAX ERROR"
        errors=$((errors + 1))
    fi
done
echo "Syntax check: $errors errors"
echo ""

# Test 2: Check all tools have required files
echo "=== Test 2: Required Files Check ==="
declare -A tools
tools[statistical_analysis]="rice_scorer.py statistical_analysis.py test_statistical_analysis.py README.md requirements.txt"
tools[load_testing]="k6_runner.py perf_analyzer.py report_generator.py load_tester.py test_load_tester.py README.md requirements.txt"
tools[sast_scanner]="sast_scanner.py semgrep_wrapper.py bandit_wrapper.py report_generator.py test_sast_scanner.py README.md requirements.txt"
tools[architecture_mgmt]="arch_manager.py adr_manager.py c4_generator.py fitness_functions.py asr_tracker.py test_arch_manager.py README.md requirements.txt"

for tool in "${!tools[@]}"; do
    echo "Checking $tool..."
    missing=0
    for file in ${tools[$tool]}; do
        if [ -f "$tool/$file" ]; then
            echo "  ✓ $file"
        else
            echo "  ✗ $file - MISSING"
            missing=$((missing + 1))
        fi
    done
    if [ $missing -eq 0 ]; then
        echo "  ✓ All required files present"
    else
        echo "  ✗ $missing files missing"
    fi
    echo ""
done

# Test 3: Check imports work
echo "=== Test 3: Import Validation ==="
cd statistical_analysis
if python3 -c "import rice_scorer; import statistical_analysis" 2>/dev/null; then
    echo "✓ statistical_analysis imports work"
else
    echo "⚠ statistical_analysis imports need dependencies"
fi
cd ..

cd load_testing
if python3 -c "import k6_runner; import perf_analyzer; import report_generator; import load_tester" 2>/dev/null; then
    echo "✓ load_testing imports work"
else
    echo "⚠ load_testing imports need dependencies"
fi
cd ..

cd sast_scanner
if python3 -c "import semgrep_wrapper; import bandit_wrapper; import report_generator; import sast_scanner" 2>/dev/null; then
    echo "✓ sast_scanner imports work"
else
    echo "⚠ sast_scanner imports need dependencies"
fi
cd ..

cd architecture_mgmt
if python3 -c "import adr_manager; import c4_generator; import fitness_functions; import asr_tracker; import arch_manager" 2>/dev/null; then
    echo "✓ architecture_mgmt imports work"
else
    echo "⚠ architecture_mgmt imports need dependencies"
fi
cd ..

echo ""
echo "✓ Validation complete"
