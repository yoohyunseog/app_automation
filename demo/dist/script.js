// 전역 변수 선언
var 스위치 = 0;
var floatingTextarea = $("#exampleFormControlTextarea");
var floatingTextarea1 = $("#exampleFormControlTextarea1");
var floatingTextarea2 = $("#exampleFormControlTextarea2");
var floatingTextarea2_1 = $("#exampleFormControlTextarea2_1");
var floatingTextarea3 = $("#exampleFormControlTextarea3");
var floatingTextarea3_1 = $("#exampleFormControlTextarea3_1");
var floatingH1 = $("#h1");

// 쿠팡 배너 데이터
/* 광고 비활성화: 쿠팡 배너 데이터 주석 처리
const coupangBanners = [
  {
    img: "https://img3a.coupangcdn.com/image/affiliate/event/promotion/2025/06/02/b0d5516c3cfd00c9018ee23b5a73002e.jpg",
    link: "https://link.coupang.com/a/cAJRGC",
    title: "💻 가전디지털, MD's pick 상반기 인기 노트북 (~12/31)"
  },
  {
    img: "https://image8.coupangcdn.com/image/affiliate/event/promotion/2024/08/16/38d26db2183900570115eeeeed21248c.png",
    link: "https://link.coupang.com/a/cAJR0D",
    title: "🎮 가전디지털, 프리미엄 게이밍 노트북"
  },
  {
    img: "https://img1c.coupangcdn.com/image/affiliate/event/promotion/2024/08/29/98593658311d00e201fbdb68ae41c32d.png",
    link: "https://link.coupang.com/a/cAJR8X",
    title: "🖥️ 가전디지털, 가성비 게이밍 모니터"
  },
  {
    img: "https://image2.coupangcdn.com/image/affiliate/event/promotion/2024/08/22/806155050edb001d014a656a5567144b.png",
    link: "https://link.coupang.com/a/cAJSg5",
    title: "🎧 가전디지털, 갤럭시 버즈"
  },
  {
    img: "https://img3a.coupangcdn.com/image/affiliate/event/promotion/2024/08/16/7cd22fb2b43900fa0115e7eeed2060c4.png",
    link: "https://link.coupang.com/a/cAJSpn",
    title: "💻 가전디지털, 게이밍 노트북"
  }
];
*/

// 링크 생성 함수들
function createYouTubeLink(value) {
  return `<a href="https://www.youtube.com/results?search_query=${encodeURIComponent(value)}" target="_blank">
    🎥 ${value}
  </a><br>`;
}

function createNaverSearchLink(value2_1) {
  return `<a href="https://search.naver.com/search.naver?query=${encodeURIComponent(value2_1)}" target="_blank">
    🔍 ${value2_1} 네이버 검색
  </a><br>`;
}

function createGoogleSearchLink(value) {
  return `<a href="https://www.google.com/search?q=${encodeURIComponent(value)}" target="_blank">
    🌐 구글 검색
  </a><br>`;
}

function createBlogLink(value, value2, value1) {
  return `<a href="https://xn--9l4b4xi9r.com/bbs/board.php?bo_table=blog&masnory&sfl=wr_subject%7C%7Cwr_content&stx=${encodeURIComponent(value)}&roa=${encodeURIComponent(value)}" target="_blank">
    📋 관련 블로그 보기
  </a><br>`;
}

function createChamsosikLink(value, value2, value1) {
  return `<a href="https://xn--9l4b4xi9r.com/bbs/board.php?bo_table=${encodeURIComponent(value2)}&sca=${encodeURIComponent(value)}&N/B&sod=${encodeURIComponent(value1)}" target="_blank">
    🌟 참소식
  </a><br>`;
}

function createDiscordLink() {
  return `<a href="https://discord.gg/TDNw2hSD" target="_blank">
    💬 K-POP / K-드라마 / 게임 트렌드 + 네이버 실시간 키워드 분석 + 자동화 커뮤니티<br>🌐 디스코드 채널 바로가기
  </a><br>`;
}

function createGitHubSponsorLink() {
  /* 광고 비활성화: GitHub 스폰서 링크 생성 주석 처리
  return `<a href="https://github.com/sponsors/yoohyunseog/card" target="_blank">
    ❤️ GitHub 후원하기
  </a><br>`;
  */
}

function createRandomCoupangBanner() {
  /* 광고 비활성화: 쿠팡 배너 생성 주석 처리
  const randomBanner = coupangBanners[Math.floor(Math.random() * coupangBanners.length)];
  return `<div style="margin: 10px 0;">
    <a href="${randomBanner.link}" target="_blank" title="${randomBanner.title}">
      ${randomBanner.title}
    </a>
  </div>`;
  */
}

// HTML 포맷팅 함수
function formatHTML(html) {
  let formatted = html;
  
  // 표준화: 다양한 <br> 변형을 '<br>'로 통일
  formatted = formatted.replace(/<br\s*\/?>/gi, '<br>');
  // 3개 이상 연속 <br> → 2개로 축약
  formatted = formatted.replace(/(?:<br>\s*){3,}/gi, '<br><br>');
  // 문서 시작/끝의 불필요한 <br> 제거
  formatted = formatted.replace(/^((\s*<br>\s*)+)/i, '');
  formatted = formatted.replace(/((\s*<br>\s*)+)$/i, '');
  
  // 복사 시 섞여 들어오는 안내 문구 제거
  const garbagePhrases = [
    '존재하지 않는 이미지입니다.',
    'AI 활용 설정',
    '사진 설명을 입력하세요.',
  ];
  garbagePhrases.forEach(t => {
    const re = new RegExp(t.replace(/[.*+?^${}()|[\]\\]/g, r => `\\${r}`), 'gi');
    formatted = formatted.replace(re, '');
  });
  
  // 빈 문단/빈 figure 정리
  formatted = formatted.replace(/<p>\s*(?:&nbsp;)?\s*<\/p>/gi, '');
  formatted = formatted.replace(/<figure[^>]*>\s*<\/figure>/gi, '');
  formatted = formatted.replace(/<figcaption[^>]*>\s*<\/figcaption>/gi, '');
  
  // 헤딩 주변 줄바꿈 정리
  formatted = formatted.replace(/((<br>\s*)+)(?=\s*<h2\b[^>]*>)/gi, '<br><br>');
  formatted = formatted.replace(/(?<!<br>\s*)(?=\s*<h2\b[^>]*>)/gi, '<br><br>');
  formatted = formatted.replace(/(<h2\b[^>]*>.*?<\/h2>)\s*<br\s*\/?>(\s*)/gi, '$1');
  formatted = formatted.replace(/((<br>\s*)+)(?=\s*<h3\b[^>]*>)/gi, '<br><br>');
  formatted = formatted.replace(/(?<!<br>\s*)(?=\s*<h3\b[^>]*>)/gi, '<br><br>');
  formatted = formatted.replace(/(<h3\b[^>]*>.*?<\/h3>)\s*<br\s*\/?>(\s*)/gi, '$1');
  // 헤딩 뒤에 과도한 <br> 축약 (최대 2개)
  formatted = formatted.replace(/(<\/h[1-6]>)(\s*(?:<br>\s*){2,})/gi, '$1<br><br>');
  
  // 문단 종료 후 줄바꿈 보장: </p> 뒤에 <br>이 없으면 추가
  formatted = formatted.replace(/<\/p>\s*(?!<br\b)/gi, '</p><br>');
  
  // 해시태그 정리
  formatted = formatted.replace(/#([^#\s]+)(?=#)/g, '#$1 ');
  formatted = formatted.replace(/#([^#\s]+)(?=#)/g, (match, p1) => `#${p1.replace('$', '')}`);
  
  return formatted;
}

// 이미지에 링크 추가 함수
function addLinksToImages(html, linkUrl) {
  return html.replace(
    /<img[^>]*>/gi,
    match => `<a href="${linkUrl}" target="_blank">${match}</a>`
  );
}

// 메인 처리 로직
setInterval(function () {
  var value = floatingTextarea.val();
  var value1 = floatingTextarea1.val();
  var value2 = floatingTextarea2.val();
  var value2_1 = floatingTextarea2_1.val();
  
  switch (스위치) {
    case 0:
      // 초기 상태: 입력값 확인
      if (value1 == value2 || value1.length == 0) {
        스위치 = 0;
      } else {
        스위치 = 1;
      }
      floatingH1.html(스위치);
      break;

    case 1:
      // 텍스트 복사
      스위치 = 2;
      floatingTextarea3.val(value1);
      floatingH1.html(스위치);
      break;

    case 2:
      // 다음 단계로 이동
      스위치 = 3;
      break;

    case 3:
      // 메인 처리
      let updated_value2 = floatingTextarea3.val();
      
      // HTML 태그 제거 및 텍스트 정리 함수
      function cleanText(text) {
        // HTML 태그 제거
        let cleanText = text.replace(/<[^>]*>/g, '');
        // HTML 엔티티 디코딩
        cleanText = cleanText.replace(/&nbsp;/g, ' ');
        cleanText = cleanText.replace(/&amp;/g, '&');
        cleanText = cleanText.replace(/&lt;/g, '<');
        cleanText = cleanText.replace(/&gt;/g, '>');
        cleanText = cleanText.replace(/&quot;/g, '"');
        cleanText = cleanText.replace(/&#39;/g, "'");
        // 연속된 공백을 하나로
        cleanText = cleanText.replace(/\s+/g, ' ');
        // 앞뒤 공백 제거
        cleanText = cleanText.trim();
        // 1000자로 제한
        if (cleanText.length > 1000) {
          cleanText = cleanText.substring(0, 1000);
          // 마지막 단어가 잘리지 않도록 조정
          const lastSpaceIndex = cleanText.lastIndexOf(' ');
          if (lastSpaceIndex > 950) {
            cleanText = cleanText.substring(0, lastSpaceIndex);
          }
          cleanText += '...';
        }
        return cleanText;
      }
      
      // value1에서 HTML 태그 제거하고 순수 텍스트 추출
      const cleanedValue1 = cleanText(updated_value2);

      // 500자 내외로 자르는 함수
      function trimTo250(text) {
        if (text.length <= 500) return text;
        let trimmed = text.substring(0, 500);
        // 마지막 단어가 잘리지 않도록 조정
        const lastSpace = trimmed.lastIndexOf(' ');
        if (lastSpace > 450) {
          trimmed = trimmed.substring(0, lastSpace);
        }
        return trimmed + '...';
      }

      // cleanedValue1을 250자 내외로 자르기
      const cleanedValue1_250 = trimTo250(floatingTextarea.val() + ' ' + cleanedValue1);
      
      // 링크 URL 생성 (정리된 텍스트 사용)
      const link_url = `https://xn--9l4b4xi9r.com/bbs/board.php?bo_table=${encodeURIComponent(value2)}&sca=${encodeURIComponent(value)}&N/B&sod=${encodeURIComponent(cleanedValue1_250)}`;
      
      // 이미지에 링크 추가
      let updated_value2_with_link = addLinksToImages(updated_value2, link_url);
      
      // HTML 포맷팅
      updated_value2_with_link = formatHTML(updated_value2_with_link);
      
      // 링크들 생성
    // 전체 문장에 포털별 검색 링크를 거는 함수들
    function wrapWithGoogleLink(query, sentence) {
      // 한글만 추출
      const koreanOnly = (query.match(/[가-힣\s]+/g) || []).join(' ').trim();
      const searchText = koreanOnly.length > 0 ? koreanOnly : query;
      const encodedQuery = encodeURIComponent(searchText);
      const url = `https://www.google.com/search?q=${encodedQuery}`;
      return `<a href="${url}" target="_blank" style="color:#0066cc; text-decoration:underline;">${sentence}</a>`;
    }

    function wrapWithBingLink(query, sentence) {
      const koreanOnly = (query.match(/[가-힣\s]+/g) || []).join(' ').trim();
      const searchText = koreanOnly.length > 0 ? koreanOnly : query;
      const encodedQuery = encodeURIComponent(searchText);
      const url = `https://www.bing.com/search?q=${encodedQuery}`;
      return `<a href="${url}" target="_blank" style="color:#0066cc; text-decoration:underline;">${sentence}</a>`;
    }

    function wrapWithNaverLink(query, sentence) {
      const koreanOnly = (query.match(/[가-힣\s]+/g) || []).join(' ').trim();
      const searchText = koreanOnly.length > 0 ? koreanOnly : query;
      const encodedQuery = encodeURIComponent(searchText);
      const url = `https://search.naver.com/search.naver?query=${encodedQuery}`;
      return `<a href="${url}" target="_blank" style="color:#0066cc; text-decoration:underline;">${sentence}</a>`;
    }
      
      // 예시 문장에 Bing 링크 적용
      const link_google_detail = wrapWithGoogleLink(cleanedValue1_250, "더 자세한 내용을 알고 싶으시다면 클릭하세요.");
      const link_bing_detail = wrapWithBingLink(cleanedValue1_250, "Bing에서 더 자세히 보기");
      const link_naver_detail = wrapWithNaverLink(cleanedValue1_250, "네이버에서 더 자세히 보기");
      //const link_discord = createDiscordLink();
      // 광고 비활성화: 쿠팡 배너 및 GitHub 스폰서 링크 생성 주석 처리
      // const link_coupang = createRandomCoupangBanner();
      // const link_github_sponsor = createGitHubSponsorLink();
      
      // 최종 HTML 조합
      const finalHTML = `
        ${updated_value2_with_link}<br>
        ${link_google_detail}<br>
        ${link_bing_detail}<br>
        ${link_naver_detail}<br>
        <a href="https://참소식.com">🌟 참소식 바로가기</a><br>
        <br>
      `;
      
      // 출력
      $('#outputArea').html(finalHTML);
      floatingTextarea3_1.val(finalHTML);
      
      // 초기화
      스위치 = 0;
      break;
  }
}, 50);

// 전체화면 출력 버튼 이벤트
$("#fullscreenOutput").on("click", function () {
  $("body").children().not(".main").hide();
});
