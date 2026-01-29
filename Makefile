export HAPLESS_DIR=./workspace/.hapless
# export HAPLESS_DEBUG=1

start:
	uv run hap-flow run ./workflows/multi_step

hap:
	uv run hap

clean:
	rm -rv ./workspace
