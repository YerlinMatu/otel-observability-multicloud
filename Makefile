.PHONY: up down smoke benchmark validate
up:
	docker compose up --build -d
down:
	docker compose down
smoke:
	./scripts/smoke-test.sh
benchmark:
	./benchmark/run.sh
validate:
	docker compose config --quiet
	python3 -m py_compile services/*.py
	python3 -m json.tool observability/grafana/dashboards/sli-dashboard.json >/dev/null
