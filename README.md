## create python virtualenv

## install mondgodb-server

## export currrent dir as python path
 ```buildoutcfg
cd test-reporter
export PYTHONPATH="${PYTHONPATH}:."
```

## start report server
```buildoutcfg
python server/app.py
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

