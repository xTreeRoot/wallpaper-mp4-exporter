(function () {
  const localeStorageKey = 'wallpaperMp4Exporter.locale';

  function normalizeLocale(value) {
    return String(value || '').toLowerCase().startsWith('zh') ? 'zh-CN' : 'en';
  }

  function detectLocale() {
    const saved = localStorage.getItem(localeStorageKey);
    const currentPath = location.pathname.toLowerCase();
    const browser = (navigator.languages && navigator.languages[0]) || navigator.language || '';
    if (currentPath.startsWith('/zh')) return 'zh-CN';
    if (currentPath.startsWith('/en')) return 'en';
    return saved || normalizeLocale(browser);
  }

  const messages = {
    en: {
      appTitle: 'Wallpaper MP4 Exporter',
      language: 'Language',
      checkingTools: 'Checking tools',
      sourcePath: 'Source file or folder',
      sourcePlaceholder: '/path/to/cache-or-media-folder',
      sourceHelp: 'This is where the app reads from: choose a wallpaper cache folder, media folder, or a single video file.',
      chooseFolder: 'Choose folder',
      chooseFile: 'Choose file',
      outputPath: 'Output path',
      outputHelp: 'Exported MP4 files, covers, manifest.json, and preview.html will be saved here.',
      chooseOutput: 'Choose output folder',
      profile: 'Read mode',
      profileHelp: 'Auto is recommended. The app tries normal media first, then known supported encrypted cache formats.',
      layout: 'Folder structure',
      layoutHelp: 'Auto detects common cache folders. Normal folder scans ordinary folders recursively.',
      compatibility: 'Playback compatibility',
      compatibilityHelp: 'Best compatibility is recommended for using the MP4 as wallpaper or playing it on more devices.',
      limit: 'Limit',
      limitHelp: 'Maximum number to export. 0 means export everything. Use 1 or 2 for a quick test run.',
      advancedOptions: 'Advanced options',
      aesKey: 'Encryption key',
      aesPlaceholder: 'text:, hex:, base64:, or raw text',
      aesHelp: 'Usually leave this empty. Auto mode already handles known supported encrypted caches. Fill it only when you know a cache needs a custom key.',
      auto: 'Auto',
      autoRecommended: 'Auto (recommended)',
      plainMedia: 'Plain media',
      manualEncryptedCache: 'Manual encrypted cache',
      iwallpaperCache: 'iWallpaper cache',
      iwallpaperCacheLayout: 'iWallpaper-style cache',
      generic: 'Generic',
      genericFolder: 'Normal folder',
      universal: 'Universal H.264',
      universalFriendly: 'Best compatibility MP4',
      macRemux: 'Mac remux',
      macFast: 'Mac fast package',
      copyStreams: 'Copy streams',
      copyOriginal: 'Keep original streams',
      overwrite: 'Overwrite existing MP4 files',
      scan: 'Scan',
      exportMp4: 'Export MP4',
      preview: 'Preview',
      exportedVideo: 'Exported video',
      noExportedVideo: 'No exported video',
      noPreviewHtml: 'No preview HTML yet',
      log: 'Log',
      idle: 'Idle',
      ready: 'Ready.',
      files: 'Files',
      found: '{count} found',
      emptyScan: 'Scan a source path to list matching files.',
      noMatches: 'No matching video files.',
      video: 'Video',
      cover: 'Cover',
      current: 'Current',
      yes: 'Yes',
      scanning: 'Scanning...',
      layoutFound: 'Layout: {layout}\nFound: {count}',
      starting: 'Starting',
      startingExport: 'Starting export...',
      failed: 'Failed',
      exportFailed: 'Export failed',
      exportedCount: '{count} exported',
      fallbackVideo: 'video',
      ffmpegReady: 'ffmpeg ready',
      ffmpegMissing: 'ffmpeg missing',
      toolCheckFailed: 'Tool check failed',
      pickingPath: 'Opening the system path picker...',
      pathPickerCanceled: 'Path selection canceled.',
      pathPickerFailed: 'Path picker failed: {message}',
      running: 'Running',
      done: 'Done',
      doneWithFailures: 'Done with failures'
    },
    'zh-CN': {
      appTitle: '壁纸 MP4 导出器',
      language: '语言',
      checkingTools: '正在检查依赖',
      sourcePath: '来源文件/文件夹',
      sourcePlaceholder: '选择壁纸缓存目录、媒体目录或单个视频文件',
      sourceHelp: '这里就是程序读取的位置：可以选壁纸软件缓存目录、普通视频文件夹，也可以选单个视频文件。',
      chooseFolder: '选择文件夹',
      chooseFile: '选择文件',
      outputPath: '输出路径',
      outputHelp: '导出的 MP4、封面图、manifest.json 和 preview.html 都会保存到这里。',
      chooseOutput: '选择输出目录',
      profile: '文件读取方式',
      profileHelp: '建议保持自动识别。程序会先尝试普通视频，再尝试已支持的加密缓存格式。',
      layout: '文件夹结构',
      layoutHelp: '建议保持自动识别。普通文件夹会递归扫描里面的视频。',
      compatibility: '播放兼容性',
      compatibilityHelp: '建议选择“最大兼容 MP4”，更适合作为动态壁纸或在更多播放器里播放。',
      limit: '导出数量',
      limitHelp: '最多导出多少个。0 表示导出全部；想先试一下可以填 1 或 2。',
      advancedOptions: '高级选项',
      aesKey: '加密密钥',
      aesPlaceholder: 'text:、hex:、base64: 或原始文本',
      aesHelp: '通常留空。自动识别已经会处理已支持的加密缓存；只有你明确知道某个缓存需要自定义密钥时才填写。',
      auto: '自动识别',
      autoRecommended: '自动识别（推荐）',
      plainMedia: '普通媒体',
      manualEncryptedCache: '手动加密缓存',
      iwallpaperCache: 'iWallpaper 缓存',
      iwallpaperCacheLayout: 'iWallpaper 风格缓存',
      iwallpaperCompatible: 'iWallpaper 兼容',
      generic: '通用目录',
      genericFolder: '普通文件夹',
      universal: '通用 H.264',
      universalFriendly: '最大兼容 MP4',
      macRemux: 'Mac 优先无损封装',
      macFast: 'Mac 快速封装',
      copyStreams: '复制原始音视频流',
      copyOriginal: '保留原始音视频',
      overwrite: '覆盖已存在的 MP4 文件',
      scan: '扫描',
      exportMp4: '导出 MP4',
      preview: '预览',
      exportedVideo: '已导出视频',
      noExportedVideo: '暂无导出视频',
      noPreviewHtml: '暂无预览 HTML',
      log: '日志',
      idle: '空闲',
      ready: '准备就绪。',
      files: '文件',
      found: '找到 {count} 个',
      emptyScan: '扫描源路径后会在这里列出匹配文件。',
      noMatches: '没有找到匹配的视频文件。',
      video: '视频',
      cover: '封面',
      current: '当前使用',
      yes: '是',
      scanning: '正在扫描...',
      layoutFound: '目录布局：{layout}\n找到数量：{count}',
      starting: '正在启动',
      startingExport: '正在开始导出...',
      failed: '失败',
      exportFailed: '导出失败',
      exportedCount: '已导出 {count} 个',
      fallbackVideo: '视频',
      ffmpegReady: 'ffmpeg 已就绪',
      ffmpegMissing: '缺少 ffmpeg',
      toolCheckFailed: '依赖检查失败',
      pickingPath: '正在打开系统路径选择框...',
      pathPickerCanceled: '已取消路径选择。',
      pathPickerFailed: '路径选择失败：{message}',
      running: '运行中',
      done: '完成',
      doneWithFailures: '完成，有失败项'
    }
  };

  function translate(locale, key, values = {}) {
    const normalized = normalizeLocale(locale);
    const template = (messages[normalized] && messages[normalized][key]) || messages.en[key] || key;
    return template.replace(/\{(\w+)\}/g, (_match, name) => values[name] ?? '');
  }

  const initialLocale = normalizeLocale(detectLocale());
  document.documentElement.lang = initialLocale;

  window.WallpaperMp4I18n = Object.freeze({
    initialLocale,
    localeStorageKey,
    messages,
    normalizeLocale,
    translate
  });
})();
