# SCOT4 API

## Build and Deploy

**To build images for testing**: push code to the default branch of this repository. The CI pipeline will create a new image and push it to the [unsorted container registry](https://baltig.sandia.gov/scot/scot4/SCOT-API/container_registry/313) with a tag matching the short SHA of the commit.

**To build an image for quality**: [identify the pipeline created by your latest push](https://baltig.sandia.gov/scot/scot4/SCOT-API/-/pipelines). Click the play button the "Tag Qual Image" job. This will take the image and push it to the [quality container registry](https://baltig.sandia.gov/scot/scot4/SCOT-API/container_registry/326) as tag `latest`. 

**To build an image for production**: [create a new release for this project](https://baltig.sandia.gov/scot/scot4/SCOT-API/-/releases). When selecting a tag, choose a new tag name that follows a valid semantic versioning scheme (MAJOR.MINOR.PATCH) for instance 1.0.17. Make sure that this version is greater than any previous release. **Note**: only a maintainer of this repository may create a patch for the default branch. Once the image is created, it will be placed in [the production container registry](https://baltig.sandia.gov/scot/scot4/SCOT-API/container_registry/340) with a tag name matching the git tag created as well as overwriting `latest`.

On tag validity: a job is run in the pipeline that verifies the tag is a valid semantic version string and is greater than any version before this one. This script lives in [SCOT4 Pipeline Support Repo](https://baltig.sandia.gov/scot/scot4/pipeline-support/-/blob/main/scripts/tag_validate.py?ref_type=heads) and is bundled into a container image for use in pipelines. It utilizes the gitlab release api to check all of the repo's releases and the git tags associated with them

#### Initial Setup 

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

#### Running

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

What needs to be done/thought about 

Roles & Permissions
* Administrator - Full Access
* Incident Commander - View Edit Events, Alerts
* Observer - View Events 

schemas need:
* PositiveInt
* EmailStr
* AnyUrl
* None
* Fix for 

DB models
* need to be pluralized 
