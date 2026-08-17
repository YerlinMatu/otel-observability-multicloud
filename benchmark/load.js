import http from 'k6/http';
import { check, sleep } from 'k6';
export const options = {
  scenarios: {steady: {executor: 'constant-vus', vus: Number(__ENV.VUS || 20), duration: __ENV.DURATION || '60s'}},
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
  thresholds: {http_req_failed: ['rate<0.01'], http_req_duration: ['p(99)<1000']},
};
export default function () {
  const r = http.get(`${__ENV.BASE_URL || 'http://host.docker.internal:8080'}/orders/${__VU}-${__ITER}`);
  check(r, {'status 200': x => x.status === 200});
  sleep(0.1);
}
