const BACKEND = 'http://fitness-backend:8000';

async function proxy(event) {
  const { request, params, url } = event;
  const target = `${BACKEND}/${params.path}${url.search}`;

  const headers = new Headers(request.headers);
  headers.delete('host');

  const init = {
    method: request.method,
    headers
  };

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    init.body = await request.arrayBuffer();
  }

  const response = await fetch(target, init);
  return new Response(response.body, {
    status: response.status,
    headers: response.headers
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
