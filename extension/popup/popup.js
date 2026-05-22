// Popup script for OpAssist extension

const DEFAULT_API_URL = 'http://localhost:8000';

async function getApiUrl() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(['apiUrl'], (result) => {
      resolve(result.apiUrl || DEFAULT_API_URL);
    });
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  const statusEl = document.getElementById('status');
  const saveBtn = document.getElementById('saveBtn');
  const savedListEl = document.getElementById('savedList');
  const API_URL = await getApiUrl();

  // Check current tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const url = tab?.url || '';

  const isSupported = [
    'devfolio.co',
    'unstop.com',
    'hackerearth.com',
  ].some(domain => url.includes(domain));

  if (isSupported) {
    statusEl.textContent = 'Supported site detected!';
    statusEl.className = 'status success';
    saveBtn.disabled = false;

    saveBtn.addEventListener('click', async () => {
      saveBtn.disabled = true;
      saveBtn.textContent = 'Saving...';

      // Send message to content script to extract data
      const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
      chrome.tabs.sendMessage(activeTab.id, { action: 'extractOpportunity' }, async (response) => {
        if (response?.data) {
          try {
            await fetch(`${API_URL}/api/opportunities`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(response.data),
            });
            saveBtn.textContent = 'Saved!';
            statusEl.textContent = 'Opportunity saved successfully!';
          } catch (err) {
            saveBtn.textContent = 'Error';
            statusEl.textContent = 'Failed to save. Is the backend running?';
            statusEl.className = 'status error';
          }
        } else {
          saveBtn.textContent = 'No data found';
        }
        setTimeout(() => {
          saveBtn.disabled = false;
          saveBtn.textContent = 'Save to OpAssist';
        }, 2000);
      });
    });
  } else {
    statusEl.textContent = 'Navigate to Devfolio, Unstop, or HackerEarth to save opportunities.';
    statusEl.className = 'status info';
  }

  // Load recent saved items
  try {
    const res = await fetch(`${API_URL}/api/opportunities?limit=5`);
    const data = await res.json();
    if (data.data?.length) {
      savedListEl.innerHTML = '<div style="font-size:12px;color:#737373;margin-bottom:4px;">Recent:</div>' +
        data.data.map(opp =>
          `<div class="saved-item">${opp.title}</div>`
        ).join('');
    }
  } catch {
    // Backend not available
  }
});
