.PHONY: check test clean

#: Same thing as test
check: test

#: Run tests
test:
	py.test test/test_all.py

clean:
	cd test && make clean
