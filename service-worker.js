//const PARTSELECT_ORIGIN = 'https://www.partselect.com';

// Allows users to open the side panel by clicking on the action toolbar icon
chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error(error));

/* 
chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
  if (!tab.url) return;
  const url = new URL(tab.url);
  // Enables the side panel on partselect.com
  if (url.origin.includes(PARTSELECT_ORIGIN)) {
    await chrome.sidePanel.setOptions({
      tabId,
      path: 'index.html',
      enabled: true
    });
  } else {
    // Disables the side panel on all other sites
    await chrome.sidePanel.setOptions({
      tabId,
      enabled: false
    });
  }
}); */

chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
  // Always enable the side panel regardless of the site
  await chrome.sidePanel.setOptions({
    tabId,
    path: 'public/index.html',
    enabled: true
  });
});