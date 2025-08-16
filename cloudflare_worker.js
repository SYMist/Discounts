// 클라우드플레어 Workers Script
// URL 리다이렉트 처리

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  const pathname = url.pathname
  
  // 기존 이벤트 URL 패턴 확인
  if (pathname.startsWith('/pages/event-') && pathname.endsWith('.html')) {
    const newUrl = getNewUrl(pathname)
    if (newUrl) {
      // 301 영구 리다이렉트
      return Response.redirect(newUrl, 301)
    }
  }
  
  // 리다이렉트가 아닌 경우 원래 요청 처리
  return fetch(request)
}

function getNewUrl(oldPath) {
  // URL 매핑 테이블
  const urlMappings = {
    "/pages/event-609b0810f_02.html": "/spaceone/썸머-놀캉스-특집-바운스-트램폴린-8월-특별-프로모션",
    "/pages/event-ab4536492c17.html": "/spaceone/나이키-유나이트-추가-할인-프로모션",
    "/pages/event-0053227c91f9.html": "/songdo/컨템포러리-ss-시즌오프-특가-제안",
    "/pages/event-0080d56b7c9a.html": "/spaceone/popup-피네플리츠",
    "/pages/event-0144aa04064f.html": "/spaceone/현대홈쇼핑-2025-summer-black-friday",
    "/pages/event-18d811f187cd.html": "/spaceone/골든듀-36주년-창립-특가-행사",
    "/pages/event-6367ceaf39ad.html": "/gimpo/버버리-스페셜-프로모션",
    "/pages/event-825489a14_02.html": "/songdo/락앤락-최대-70-창고-개방전",
    "/pages/event-39c753a8f850.html": "/spaceone/스페이스원-최초-살로몬윌슨-단독특가전-살로몬-최대-60",
    "/pages/event-220bcae65_02.html": "/songdo/마리떼프랑소와저버-여름-특가-제안"
  }
  
  return urlMappings[oldPath] || null
} 