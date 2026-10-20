# SCOT4 API

## Initial Setup 

Create a .env

```shell
touch src/.env
```

Needs to contain these keys
```
# PROD or DEV
ENV=
SECRET_KEY=
SQLALCHEMY_DATABASE_URI=sqlite:///../scot4-test.db
```

Note `main.py` ts called from the TLD.
```shell
export PYTHONPATH=$PWD/src
python src/app/main.py
```

## Running

Using main
```shell
python src/app/main.py
```

**OR**
Using uvicorn
```shell
export PYTHONPATH=$PWD/src
cd src/app
uvicorn main:app --host=127.0.0.1 --port=8080 --reload
```


#### Running Tests
Now in parallel!
- With `-n auto`, pytest-xdist will use as many processes as your computer has physical CPU cores.
-  `--dist loadfile`: Tests are grouped by their containing file. Groups are distributed to available workers as whole units. This guarantees that all tests in a file run in the same worker.
- Make sure that the SQLite database is in memory otherwise it can crash

```shell
export PYTHONPATH=$PWD/src:$PWD/tests
export SQLALCHEMY_DATABASE_URI="sqlite://"
export ENV=TEST
pytest -n auto --dist loadfile tests/
```

To run pytest normally
```shell
export PYTHONPATH=$PWD/src:$PWD/tests
pytest tests/
```
