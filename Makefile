default : manual check

check :
	python3 src/python/check.py --no-warn-incomplete data/prince/prince.cusf
	python3 src/python/check.py --no-warn-incomplete data/pud/de/00.cusf
	python3 src/python/check.py --no-warn-incomplete data/pud/en/01.cusf
	python3 src/python/check.py --no-warn-incomplete data/1984/de/000.cusf
	python3 src/python/check.py --no-warn-incomplete data/1984/de/001.cusf
	python3 src/python/check.py --no-warn-incomplete data/1984/de/002.cusf
	python3 src/python/check.py --no-warn-incomplete data/1984/de/003.cusf
	python3 src/python/check.py --no-warn-incomplete data/1984/de/004.cusf
	python3 src/python/check.py --no-warn-incomplete data/1984/de/005.cusf
	python3 src/python/check.py --no-warn-incomplete data/1984/de/006.cusf
	python3 src/python/check.py --no-warn-incomplete data/1984/de/007.cusf
	python3 src/python/check.py --no-warn-incomplete data/1984/de/008.cusf
	python3 src/python/check.py --no-warn-incomplete data/1984/de/009.cusf
	python3 src/python/check.py --no-warn-incomplete data/1984/de/010.cusf

manual :
	cd doc/manual; make manual.pdf
