/**
 * Content script injected on GitHub repo pages.
 * Detects the current repo URL and injects the RepoLens trigger button.
 */

function getRepoUrl() {
  const match = window.location.pathname.match(/^\/([^/]+)\/([^/]+)/);
  if (match) return `https://github.com${match[0]}`;
  return null;
}

function injectButton() {
  // TODO: inject a "RepoLens" button into the GitHub repo header UI
  // On click → send ANALYZE_REPO message to background.js
}

if (getRepoUrl()) injectButton();
