SHELL := /bin/sh

.PHONY: help uv-setup uv-update run-backend alembic-rev alembic-up compose-up compose-down

# Forward common targets to the repository root Makefile
help uv-setup uv-update run-backend alembic-rev alembic-up compose-up compose-down:
	$(MAKE) -C .. $@ AUTOGEN="$(AUTOGEN)"
