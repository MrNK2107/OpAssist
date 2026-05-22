// Content script — extracts opportunity data from supported sites

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractOpportunity') {
    const data = extractFromPage();
    sendResponse({ data });
  }
  return true;
});

function extractFromPage() {
  const url = window.location.href;

  if (url.includes('devfolio.co')) {
    return extractDevfolio();
  }
  if (url.includes('unstop.com')) {
    return extractUnstop();
  }
  if (url.includes('hackerearth.com')) {
    return extractHackerEarth();
  }

  return null;
}

function extractDevfolio() {
  const title = document.querySelector('h1')?.textContent?.trim() ||
                document.querySelector('[class*="title"]')?.textContent?.trim() || '';
  if (!title) return null;

  return {
    title,
    type: 'hackathon',
    url: window.location.href,
    source: 'devfolio',
    description: document.querySelector('[class*="description"], [class*="tagline"]')?.textContent?.trim() || '',
    organizer: document.querySelector('[class*="organizer"], [class*="hosted"]')?.textContent?.trim() || '',
    location: document.querySelector('[class*="location"]')?.textContent?.trim() || 'Online',
    tags: Array.from(document.querySelectorAll('[class*="theme"], [class*="tag"]')).map(el => el.textContent.trim()).filter(Boolean),
  };
}

function extractUnstop() {
  const title = document.querySelector('h1')?.textContent?.trim() ||
                document.querySelector('[class*="title"]')?.textContent?.trim() || '';
  if (!title) return null;

  return {
    title,
    type: classifyType(title),
    url: window.location.href,
    source: 'unstop',
    description: document.querySelector('[class*="description"]')?.textContent?.trim() || '',
    organizer: document.querySelector('[class*="organiz"]')?.textContent?.trim() || '',
    location: document.querySelector('[class*="location"]')?.textContent?.trim() || 'Online',
  };
}

function extractHackerEarth() {
  const title = document.querySelector('h1')?.textContent?.trim() ||
                document.querySelector('[class*="title"]')?.textContent?.trim() || '';
  if (!title) return null;

  return {
    title,
    type: classifyType(title),
    url: window.location.href,
    source: 'hackerearth',
    description: document.querySelector('[class*="description"]')?.textContent?.trim() || '',
  };
}

function classifyType(title) {
  const lower = title.toLowerCase();
  if (lower.includes('intern')) return 'internship';
  if (lower.includes('scholar')) return 'scholarship';
  if (lower.includes('hack')) return 'hackathon';
  return 'event';
}
