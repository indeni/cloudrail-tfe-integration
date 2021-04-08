** Deployment

We install the cli package from virtual repo ‘cloudrail-cli-pypi’
This repo is pointed to 1 repo: ‘cloudrail-cli-pypi-release’
Our build deploys a new package to repo ‘cloudrail-cli-pypi-develop’.
So, if you want to install new version of the package from repo ‘cloudrail-cli-pypi’, it should exist in repo ‘cloudrail-cli-pypi-release’.
In other words we should "release" the package using job "Cloudrail-CD/Cloudrail-release-CLI".
This job copies the package from ‘cloudrail-cli-pypi-develop’ to ‘cloudrail-cli-pypi-release’


** Install Cloudrail CLI

```
    pip3 install "cloudrail==x.y.z" --extra-index-url https://indeni.jfrog.io/indeni/api/pypi/cloudrail-cli-pypi/simple
    or
    pip3 install cloudrail --extra-index-url https://indeni.jfrog.io/indeni/api/pypi/cloudrail-cli-pypi/simple
```

** Install not released version of Cloudrail CLI

```
    pip3 install "cloudrail==x.y.z" --extra-index-url https://indeni.jfrog.io/indeni/api/pypi/cloudrail-cli-pypi-develop/simple
    or
    pip3 install cloudrail --extra-index-url https://indeni.jfrog.io/indeni/api/pypi/cloudrail-cli-pypi-develop/simple
```
