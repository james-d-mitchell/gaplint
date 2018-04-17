coverage:
	@coverage run --source gaplint -m py.test
	@coverage html
	@echo "See: htmlcov/index.html" 

clean: 
	rm -rf htmlcov
	rm -f *.pyc
	rm -f *.pyo
	rm -f restats

profile:
	profile/profile.py

.PHONY: profile
