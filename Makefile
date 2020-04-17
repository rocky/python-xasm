.PHONY: check test clean

GIT2CL ?= git2cl
PYTHON ?= python
PYTHON3 ?= python3
RM      ?= rm
LINT    = flake8

#: Same thing as test
check: test

#: Run tests
test:
	py.test pytest
	py.test test/test_all.py

clean:
	cd test && make clean

#: Make eggs, wheels and tarball
dist: test
	./admin-tools/make-dist.sh

rmChangeLog:
	rm ChangeLog || true

#: Create a ChangeLog from git via git log and git2cl
ChangeLog: rmChangeLog
	git log --pretty --numstat --summary | $(GIT2CL) >$@
