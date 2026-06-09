(function () {
  async function request(path, options = {}) {
    const response = await fetch(path, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || response.statusText);
    }
    return payload;
  }

  function mediaUrl(path) {
    return `/api/media?path=${encodeURIComponent(path)}`;
  }

  window.WallpaperMp4Api = Object.freeze({
    mediaUrl,
    request
  });
})();
