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

## Macros
* JENKINS_ARTIFACT_URL points to "http://<jenkins_build_url>/<build_number>/artifact"