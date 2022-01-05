ifneq (,$(wildcard ./.env))
    include .env
    export
endif

.DEFAUL_GOAL := list
.PHONY: list

list: ## -- list all the targets in this file with a description
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' Makefile \
	| sed -n 's/^\(.*\): \(.*\)##\(.*\)/\1\3/p'

clean: clean-cdk clean-layer ## -- rm cdk, layer, and venv
.PHONY: clean

layer: clean-layer pip-layer zip-layer ## -- build clean layer zip
.PHONY: layer

deploy:
	@ echo "deploying stack"
	@ cdk deploy --all --force

hotswap:
	@ echo "deploying stack -- hotswap"
	@ cdk deploy --all --force --hotswap

pip-layer: ## -- install reqs into local dir for layer
	@ echo "installing python requirements for layers"
	@ if [ ! -d layers/python ]; then mkdir -p layers/python/lib/python3.9/site-packages; fi
	@ source venv/bin/activate; pip install -U -t layers/python/lib/python3.9/site-packages/ -r layers/requirements.txt

zip-layer: ## -- zip up the layer packages for asset deployment
	@ echo "creating zip file of layer requirements"
	@ cd layers; zip -r stepfunctions.zip .

clean-cdk: ## -- clean the cdk.out dir
	@ echo "removing cdk.out"
	@ rm -rf cdk.out

clean-layer: ## -- clean the layer libs
	@ echo "removing layer libs"
	@ cd layers; rm -rf python; rm *.zip

lint:
	(\
		black data_pipeline_deploy; \
		black lambdas; \
		isort data_pipeline_deploy; \
		isort lambdas; \
	)
