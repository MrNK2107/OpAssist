// Background service worker for OpAssist extension

const DEFAULT_API_URL = 'http://localhost:8000';

async function getApiUrl() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['apiUrl'], (result) => {
      resolve(result.apiUrl || DEFAULT_API_URL);
    });
  });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'saveOpportunity') {
    saveOpportunity(request.data)
      .then(sendResponse)
      .catch(err => sendResponse({ error: err.message }));
    return true; // Keep channel open for async response
  }
});

async function saveOpportunity(data) {
  const API_URL = await getApiUrl();
  const response = await fetch(`${API_URL}/api/opportunities`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}
