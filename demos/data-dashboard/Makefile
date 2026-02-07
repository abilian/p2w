# Data Dashboard Demo Makefile

.PHONY: build serve clean run

# Build WASM from Python
build:
	@echo "Compiling app.py to WASM..."
	@mkdir -p dist
	@cd ../../.. && uv run python -c "\
from p2w.compiler import compile_to_wat; \
from p2w.runner import wat_to_wasm; \
source = open('demos/data-dashboard/p2w/app.py').read(); \
wat = compile_to_wat(source); \
wasm = wat_to_wasm(wat); \
open('demos/data-dashboard/p2w/dist/app.wasm', 'wb').write(wasm); \
print('Built dist/app.wasm -', len(wasm), 'bytes')"

# Start local server
serve:
	@echo "Starting server at http://localhost:8000"
	@python -m http.server 8000

# Clean build artifacts
clean:
	@rm -rf dist/*.wasm
	@echo "Cleaned build artifacts"

# Build and serve
run: build serve
