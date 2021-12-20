coverage:
	@coverage run --source gaplint -m py.test
	@coverage html
	@echo "See: htmlcov/index.html" 

clean: 
	git clean -xdf --exclude *.swp --exclude *.swo

check: 
	tox

lint: 
	pylint gaplint.py setup.py
