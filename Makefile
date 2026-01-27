export HAPLESS_DIR=./workspace/.hapless
# export HAPLESS_DEBUG=1

start:
	uv run hap-flow execute-workflow ./workspace ./workflows/multi_step adhoc

hap:
	uv run hap

clean:
	rm -rv ./workspace
