# export HAPLESS_DEBUG=1

start:
	uv run hap-flow run ./workflows/multi_step

clean:
	rm -rv ./workspace
