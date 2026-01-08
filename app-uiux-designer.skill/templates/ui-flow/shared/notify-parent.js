// Notify parent window about current page for device-preview sync
// Include this script in all screen HTML files: <script src="../shared/notify-parent.js"></script>
(function() {
  if (window.parent && window.parent !== window) {
    // Send current URL to parent
    window.parent.postMessage({
      type: 'pageLoaded',
      url: window.location.href,
      pathname: window.location.pathname
    }, '*');
  }
})();
