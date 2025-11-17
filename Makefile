# IBCo PDF Stripper - Makefile
# Provides convenient commands for common operations

.PHONY: help install test clean activate

# Default target
help:
	@echo "IBCo PDF Stripper - Available Commands"
	@echo "======================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          Run first-time setup"
	@echo "  make install-dev      Install with development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run comprehensive test suite"
	@echo "  make test-all         Run all test files"
	@echo "  make test-quick       Run quick verification tests"
	@echo ""
	@echo "Usage:"
	@echo "  make activate         Show activation instructions"
	@echo "  make example          Show usage examples"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            Remove generated files"
	@echo "  make clean-all        Remove venv and all generated files"
	@echo ""

# Installation
install:
	@echo "Running setup script..."
	@./setup.sh

install-dev: install
	@echo "Installing development dependencies..."
	@. venv/bin/activate && pip install pytest pytest-cov black mypy
	@echo "✓ Development environment ready"

# Testing
test:
	@echo "Running comprehensive test suite..."
	@. venv/bin/activate && python tests/run_all_tests.py

test-all:
	@echo "Running all test files..."
	@. venv/bin/activate && \
		for test in test_*.py; do \
			echo ""; \
			echo "Running $$test..."; \
			python $$test || exit 1; \
		done
	@echo ""
	@echo "✓ All tests completed"

test-quick:
	@echo "Running quick verification..."
	@. venv/bin/activate && python -c "import ibco_stripper; print('✓ Core module OK')"
	@. venv/bin/activate && python -c "import config; print('✓ Config module OK')"
	@echo "✓ Quick verification passed"

# Usage help
activate:
	@echo "To activate the virtual environment:"
	@echo ""
	@echo "  source venv/bin/activate"
	@echo ""
	@echo "Or use the convenience script:"
	@echo ""
	@echo "  source activate_cafr.sh"
	@echo ""

example:
	@echo "Example Usage:"
	@echo "=============="
	@echo ""
	@echo "1. Activate environment:"
	@echo "   source venv/bin/activate"
	@echo ""
	@echo "2. Process a single CAFR:"
	@echo "   python ibco_stripper.py \\"
	@echo "     --pdf ~/workspace/ibco/pdfs/city_2024.pdf \\"
	@echo "     --toc ~/workspace/ibco/toc_screenshots/toc.png \\"
	@echo "     --output ~/workspace/ibco/output/city_2024/"
	@echo ""
	@echo "3. Process multiple years:"
	@echo "   python process_city.py \\"
	@echo "     --config ~/workspace/ibco/config/city_config.yaml"
	@echo ""
	@echo "4. Verify output:"
	@echo "   python -c \"from ibco_stripper import PDFStripper; \\"
	@echo "     s = PDFStripper('pdf.pdf', 'out/'); \\"
	@echo "     s.verify_processing()\""
	@echo ""

# Cleaning
clean:
	@echo "Cleaning generated files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache 2>/dev/null || true
	@rm -f /tmp/cafr_test_output.log 2>/dev/null || true
	@echo "✓ Cleaned generated files"

clean-all: clean
	@echo "Removing virtual environment..."
	@rm -rf venv
	@rm -f activate_cafr.sh
	@echo "✓ Removed virtual environment"
	@echo ""
	@echo "Note: Workspace data (~/workspace/ibco) was NOT removed"
	@echo "      To remove workspace data: rm -rf ~/workspace/ibco"
