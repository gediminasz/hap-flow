export HAPLESS_DIR=./workspace/.hapless

start:
	uv run hap-flow run ./workspace ./workflows/single_file.sh adhoc

hap:
	uv run hap

hap-clean:
	uv run hap clean
