/**
 * api.js — Thin wrapper around window.pywebview.api
 * Every method returns a Promise that resolves with the Python return value.
 */

// Define __pyEvent stub early so Python threads can call it even if app.js
// hasn't executed yet. app.js will override this with the real handler.
window.__pyEvent = window.__pyEvent || function(type, data) {
  console.log('[pyEvent early]', type, data);
};

const Api = (() => {

  async function call(method, ...args) {
    try {
      if (!window.pywebview || !window.pywebview.api) {
        throw new Error('pywebview API not ready');
      }
      const result = await window.pywebview.api[method](...args);
      return result;
    } catch (err) {
      console.error(`[API] ${method} failed:`, err);
      return { success: false, error: err.message || String(err) };
    }
  }

  return {
    // Window
    minimize:       ()        => call('minimize_window'),
    toggleMaximize: ()        => call('toggle_maximize'),
    close:          ()        => call('close_window'),

    // Settings
    getSettings:    ()        => call('get_settings'),
    saveSettings:   (s)       => call('save_settings', s),

    // Validation
    validateGtav:   (p)       => call('validate_gtav', p),
    validateFivem:  (p)       => call('validate_fivem', p),

    // Dialogs
    selectFolder:   ()        => call('select_folder'),
    selectFivemExe: ()        => call('select_fivem_exe'),

    // Packs
    scanPacks:      ()        => call('scan_packs'),
    installPack:    (path)    => call('install_pack', path),
    uninstallPack:  (name)    => call('uninstall_pack', name),
    openFolder:     (path)    => call('open_folder', path),

    // Cleaners
    previewFivemClean: ()     => call('preview_fivem_clean'),
    cleanFivem:     ()        => call('clean_fivem'),
    cleanGtav:      ()        => call('clean_gtav'),

    // Baseline
    getBaselineStatus:    ()  => call('get_baseline_status'),
    createGtavBaseline:   ()  => call('create_gtav_baseline'),

    // History / Logs
    getHistory:     (n)       => call('get_history', n || 50),
    getLogs:        (n)       => call('get_logs', n || 100),

    // Workshop
    getWorkshopPacks:     ()           => call('get_workshop_packs'),
    downloadWorkshopPack: (url, name)  => call('download_workshop_pack', url, name),
    fetchImageB64:        (url)        => call('fetch_image_b64', url),
    getVideoStreamUrl:    (url)        => call('get_video_stream_url', url),

    // Updates
    checkForUpdate:       ()           => call('check_for_update'),

    // App
    getAppInfo:     ()        => call('get_app_info'),
  };

})();
