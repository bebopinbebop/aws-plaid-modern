.PHONY: setup validate test frontend build deploy format clean

setup:
	python3.13 -m venv .venv
	.venv/bin/python -m pip install -r backend/requirements-dev.txt
	npm ci --prefix frontend

validate:
	sam validate --lint
	.venv/bin/cfn-lint template.yml

test:
	.venv/bin/python -m pytest -q
	node --test backend/resolvers/tests/*.test.cjs
	npm test --prefix frontend

frontend:
	npm run build --prefix frontend

build:
	sam build --use-container --parallel

# Deployment and cleanup are explicit cloud mutations. Run only when intended.
deploy:
	sam deploy --guided

clean:
	sam delete

format:
	.venv/bin/black backend tests scripts
