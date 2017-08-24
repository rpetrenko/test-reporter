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