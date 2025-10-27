export async function onRequest(context) {
  const url = new URL(context.request.url);
  // Redirect all Pages default domains to the custom primary domain
  if (url.hostname.endsWith('.pages.dev')) {
    url.hostname = 'discounts.deluxo.co.kr';
    return Response.redirect(url.toString(), 301);
  }
  // Continue to static assets, _redirects and other handlers
  return context.next();
}

