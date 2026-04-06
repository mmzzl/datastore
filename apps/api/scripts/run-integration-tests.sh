#!/bin/bash
# Integration Test Runner for Datastore API
# Run: bash scripts/run-integration-tests.sh

echo "Running integration tests..."
echo

py -3.12 -m pytest apps/api/tests/integration/ -v

if [ $? -ne 0 ]; then
    echo
    echo "Tests failed!"
    exit 1
fi

echo
echo "All integration tests passed!"
