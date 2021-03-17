coverage:
	@coverage run --source gaplint -m py.test
	@coverage html
	@echo "See: htmlcov/index.html" 

clean: 
	git clean -xdf --exclude *.swp --exclude *.swo

.PHONY: clean

profile:
	profile/profile.py

.PHONY: profile

check: 
	tox

.PHONY: check
