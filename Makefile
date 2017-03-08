test: 
	python tests/gaplint.test.py

coverage:
	@coverage run tests/gaplint.test.py
	@coverage html
	@echo "See: htmlcov/index.html" 

clean: 
	rm -rf htmlcov
	rm -f *.pyc
