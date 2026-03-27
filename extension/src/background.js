/**
 * Background service worker.
 * Handles communication between content script and popup,
 * and makes API calls to the RepoLens backend.
 */

const BACKEND_URL = "http://localhost:8000";

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "ANALYZE_REPO") {
    analyzeRepo(msg.repoUrl).then(sendResponse);
    return true; // keep channel open for async response
  }
});

async function analyzeRepo(repoUrl) {
  try {
    const res = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: repoUrl }),
    });
    return await res.json();
  } catch (err) {
    return { error: err.message };
  }
}
