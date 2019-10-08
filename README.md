## Design notes
* jobs that are building should never enter TR database


## create python virtualenv
todo again

## install mondgodb-server


## export currrent dir as python path
 ```buildoutcfg
cd test-reporter
export PYTHONPATH="${PYTHONPATH}:."
export SECRET_KEY="some__secret__key"
```

## start report server
```buildoutcfg
python server/app.py --host 0.0.0.0 --port 5000
```

## navigate to
```buildoutcfg
http://ip:5000/api
```

## use populate DB script to start off
```buildoutcfg
# drop DB
python server/db/fetch_jenkins_info.py -D

# populate DB

```

## Notes
* don't fetch builds that are not complete (still running)

## Labels
For labels the following keywords predefined:
* BUILD_ARTIFACT_API
* BUILD_INFO_API

## Test definitions, used to organize test results
* Create definition yaml file: see example-test-definitions.yaml
* Convert yaml to json
```bash
python -c "import yaml,json,pprint;pprint.pprint(json.loads(json.dumps(yaml.load(open(\"fname.yaml\").read()))))"
```

