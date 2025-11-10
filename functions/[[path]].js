export async function onRequest(context) {
  const { request } = context;
  const url = new URL(request.url);

  // 1) Enforce primary domain for pages.dev
  if (url.hostname.endsWith('.pages.dev')) {
    url.hostname = 'discounts.deluxo.co.kr';
    return Response.redirect(url.toString(), 301);
  }

  // 2) Pretty URL → file rewrite (200) to avoid 308 redirects
  //    /{branch}/{slug} → /pages/{branch}-{slug}.html
  const m = url.pathname.match(/^\/(songdo|gimpo|spaceone)\/(.+)$/);
  if (m) {
    const branch = m[1];
    const slug = m[2];
    const newPath = `/pages/${branch}-${slug}.html`;
    const target = new URL(url.toString());
    target.pathname = newPath;
    return fetch(new Request(target.toString(), request));
  }

  return context.next();
}
