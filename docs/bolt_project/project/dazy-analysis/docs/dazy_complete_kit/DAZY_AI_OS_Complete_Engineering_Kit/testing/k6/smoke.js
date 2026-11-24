import http from 'k6/http';
import { check, sleep } from 'k6';

// Run only against a local/staging environment you own.
// Keep this intentionally small for an 8 GB workstation.
const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export const options = {
  vus: 1,
  duration: '30s',
  thresholds: {
    http_req_failed: ['rate<0.02'],
    // Set an agreed SLO after recording a baseline; this example is only a starter gate.
    http_req_duration: ['p(95)<2000'],
  },
};

export default function () {
  const res = http.get(`${BASE_URL}/health`, {
    tags: { name: 'health_smoke' },
  });

  check(res, {
    'health endpoint returns 2xx': (r) => r.status >= 200 && r.status < 300,
  });

  sleep(1);
}
