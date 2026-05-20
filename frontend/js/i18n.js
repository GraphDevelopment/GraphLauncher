/**
 * i18n.js — lightweight translation system.
 * Locales embedded directly to avoid file:// fetch issues in pywebview.
 */

const I18n = (() => {

  const SUPPORTED = ['fr', 'en'];
  const DEFAULT   = 'en';

  const LOCALES = {

    fr: {
      status_active: 'Launcher actif',
      nav_packs: 'Packs graphiques', nav_workshop: 'Workshop',
      nav_tutorial: "Guide d'utilisation", nav_settings: 'Paramètres',

      packs_title: 'Gestionnaire de packs',
      packs_subtitle: 'Installez et gérez vos packs graphiques FiveM',
      btn_scan: 'Scanner', btn_clean_fivem: 'Clean FiveM', btn_clean_gtav: 'Clean GTA V',
      stat_detected: 'Packs détectés', stat_installed: 'Installés', stat_available: 'Disponibles',
      filter_all: 'Tous', filter_installed: 'Installés', filter_not_installed: 'Non installés',
      empty_title: 'Aucun pack trouvé',
      empty_desc: 'Configurez le dossier des packs dans les Paramètres puis cliquez sur Scanner.',
      btn_open_settings: 'Ouvrir les paramètres',
      btn_install: 'Installer', btn_uninstall: 'Désinstaller', btn_open: 'Ouvrir',

      workshop_title: 'Workshop',
      workshop_subtitle: 'Téléchargez des packs depuis la communauté',
      btn_refresh: 'Actualiser', btn_download: 'Télécharger', btn_preview: 'Aperçu',
      ws_search_ph: 'Rechercher…',
      ws_empty_title: 'Aucun pack disponible',
      ws_empty_desc: 'Le workshop est vide ou inaccessible pour le moment.',
      ws_size: '{n} Mo', ws_downloads: '{n} téléchargements',

      tutorial_title: "Guide d'utilisation",
      tutorial_subtitle: 'Instructions et références pour utiliser le launcher',

      settings_title: 'Paramètres', settings_subtitle: "Chemins d'accès et configuration",
      btn_save: 'Sauvegarder',
      section_packs_dir: 'Dossier des packs',
      section_packs_dir_desc: 'Répertoire contenant vos packs graphiques. Chaque sous-dossier devient un pack détectable.',
      label_path: 'Chemin', btn_browse: 'Parcourir',
      section_fivem: 'FiveM',
      section_fivem_desc: 'Sélectionnez FiveM.exe — le dossier de données est détecté automatiquement.',
      label_fivem_data: 'FiveM Application Data (auto-détecté)', btn_select: 'Sélectionner',
      section_gtav: 'GTA V',
      section_gtav_desc: 'Le dossier doit contenir : GTA5.exe, GTAVLauncher.exe, x64b.rpf, x64v.rpf.',
      label_gtav_dir: 'Dossier GTA V',
      section_language: 'Langue', section_language_desc: "Langue de l'interface du launcher",
      section_baseline: 'Protection GTA V — Baseline',
      section_baseline_desc: "Calcule un index SHA256 de tous les fichiers officiels de GTA V. Lors du nettoyage, seuls les fichiers absents de cet index sont supprimés. À créer sur une installation propre, sans mods.",
      baseline_warning_title: 'Recommandé sur installation vierge',
      baseline_warning_desc: "L'opération peut prendre 5 à 10 minutes selon la taille du jeu.",
      btn_create_baseline: 'Créer / Mettre à jour la baseline',

      update_msg: 'Nouvelle version disponible : v{version}',
      btn_update_dl: 'Télécharger',

      confirm_cancel: 'Annuler', confirm_ok: 'Confirmer',
      modal_wait: 'Veuillez patienter',

      toast_packs_n: '{n} pack(s) détecté(s)',
      toast_no_packs_dir: 'Dossier de packs non configuré',
      toast_settings_saved: 'Paramètres sauvegardés',
      toast_fivem_ok: 'FiveM configuré',
      toast_gtav_ok: 'GTA V configuré',
      toast_folder_selected: 'Dossier sélectionné',
      toast_install_started: 'Installation démarrée',
      toast_uninstall_started: 'Désinstallation démarrée',
      toast_configure_first: 'Configurez vos dossiers pour commencer',
      toast_operation_done: 'Opération terminée',
      toast_files_n: '{n} fichier(s) traité(s)',
      toast_operation_failed: 'Opération échouée',
      toast_busy: 'Une opération est déjà en cours',
      toast_need_gtav: "Configurez d'abord le dossier GTA V",
      toast_download_ok: 'Pack téléchargé avec succès',
      toast_workshop_error: 'Impossible de charger le workshop. Vérifiez votre connexion.',
      toast_no_packs_dir_ws: "Configurez d'abord le dossier des packs dans les Paramètres",
      toast_lang_changed: 'Langue mise à jour',

      valid_checking: 'Validation en cours…',
      valid_fivem_ok: 'Valide — dossier de données : {dir}',
      valid_gtav_ok: 'Dossier GTA V valide',
      valid_checking_gtav: 'Validation…',

      confirm_uninstall_title: 'Désinstaller le pack',
      confirm_uninstall_desc: '« {name} » — supprimer tous les fichiers installés ?',
      confirm_clean_fivem_title: 'Nettoyer FiveM',
      confirm_clean_fivem_desc: 'Supprimer mods, plugins, ReShade et fichiers de packs dans FiveM Application Data ?',
      confirm_clean_gtav_title: 'Nettoyer GTA V',
      confirm_clean_gtav_desc: 'Supprimer les fichiers de mods dans GTA V (les fichiers officiels sont protégés par la baseline) ?',
      confirm_baseline_title: 'Créer la baseline GTA V',
      confirm_baseline_desc: "Analyse tous les fichiers officiels de GTA V (5–10 min). À faire sur une installation sans mods.",
      confirm_download_title: 'Télécharger le pack',
      confirm_download_desc: '« {name} » sera téléchargé et extrait dans votre dossier de packs.',

      op_installing: 'Installation du pack', op_uninstalling: 'Désinstallation',
      op_clean_fivem: 'Nettoyage FiveM', op_clean_gtav: 'Nettoyage GTA V',
      op_baseline: 'Création de la baseline GTA V', op_downloading: 'Téléchargement du pack',

      scanning: 'Scan…', installing: 'Démarrage…', uninstalling: 'Suppression…',
      cleaning: 'Nettoyage…', downloading: 'Téléchargement…', saving: 'Sauvegarde…',

      baseline_none: 'Aucune baseline créée',
      baseline_ok: 'Baseline présente — {n} fichiers indexés',
    },

    en: {
      status_active: 'Launcher active',
      nav_packs: 'Graphic packs', nav_workshop: 'Workshop',
      nav_tutorial: 'User guide', nav_settings: 'Settings',

      packs_title: 'Pack manager',
      packs_subtitle: 'Install and manage your FiveM graphic packs',
      btn_scan: 'Scan', btn_clean_fivem: 'Clean FiveM', btn_clean_gtav: 'Clean GTA V',
      stat_detected: 'Detected packs', stat_installed: 'Installed', stat_available: 'Available',
      filter_all: 'All', filter_installed: 'Installed', filter_not_installed: 'Not installed',
      empty_title: 'No packs found',
      empty_desc: 'Configure the packs folder in Settings then click Scan.',
      btn_open_settings: 'Open settings',
      btn_install: 'Install', btn_uninstall: 'Uninstall', btn_open: 'Open',

      workshop_title: 'Workshop',
      workshop_subtitle: 'Download packs from the community',
      btn_refresh: 'Refresh', btn_download: 'Download', btn_preview: 'Preview',
      ws_search_ph: 'Search…',
      ws_empty_title: 'No packs available',
      ws_empty_desc: 'The workshop is empty or unreachable.',
      ws_size: '{n} MB', ws_downloads: '{n} downloads',

      tutorial_title: 'User guide',
      tutorial_subtitle: 'Instructions and references for the launcher',

      settings_title: 'Settings', settings_subtitle: 'Paths and configuration',
      btn_save: 'Save',
      section_packs_dir: 'Packs folder',
      section_packs_dir_desc: 'Directory containing your graphic packs. Each subfolder becomes a detectable pack.',
      label_path: 'Path', btn_browse: 'Browse',
      section_fivem: 'FiveM',
      section_fivem_desc: 'Select FiveM.exe — the data folder is auto-detected.',
      label_fivem_data: 'FiveM Application Data (auto-detected)', btn_select: 'Select',
      section_gtav: 'GTA V',
      section_gtav_desc: 'The folder must contain: GTA5.exe, GTAVLauncher.exe, x64b.rpf, x64v.rpf.',
      label_gtav_dir: 'GTA V folder',
      section_language: 'Language', section_language_desc: 'Interface language for the launcher',
      section_baseline: 'GTA V Protection — Baseline',
      section_baseline_desc: 'Calculates a SHA256 index of all official GTA V files. Only files absent from this index are deleted when cleaning. Run on a clean installation without mods.',
      baseline_warning_title: 'Recommended on a clean install',
      baseline_warning_desc: 'The operation may take 5 to 10 minutes depending on game size.',
      btn_create_baseline: 'Create / Update baseline',

      update_msg: 'New version available: v{version}',
      btn_update_dl: 'Download',

      confirm_cancel: 'Cancel', confirm_ok: 'Confirm',
      modal_wait: 'Please wait',

      toast_packs_n: '{n} pack(s) detected',
      toast_no_packs_dir: 'Packs folder not configured',
      toast_settings_saved: 'Settings saved',
      toast_fivem_ok: 'FiveM configured',
      toast_gtav_ok: 'GTA V configured',
      toast_folder_selected: 'Folder selected',
      toast_install_started: 'Installation started',
      toast_uninstall_started: 'Uninstall started',
      toast_configure_first: 'Configure your folders to get started',
      toast_operation_done: 'Operation complete',
      toast_files_n: '{n} file(s) processed',
      toast_operation_failed: 'Operation failed',
      toast_busy: 'An operation is already in progress',
      toast_need_gtav: 'Configure the GTA V folder first',
      toast_download_ok: 'Pack downloaded successfully',
      toast_workshop_error: 'Failed to load workshop. Check your connection.',
      toast_no_packs_dir_ws: 'Configure the packs folder in Settings first',
      toast_lang_changed: 'Language updated',

      valid_checking: 'Validating…',
      valid_fivem_ok: 'Valid — data folder: {dir}',
      valid_gtav_ok: 'GTA V folder valid',
      valid_checking_gtav: 'Validating…',

      confirm_uninstall_title: 'Uninstall pack',
      confirm_uninstall_desc: '« {name} » — delete all installed files?',
      confirm_clean_fivem_title: 'Clean FiveM',
      confirm_clean_fivem_desc: 'Remove mods, plugins, ReShade and pack files from FiveM Application Data?',
      confirm_clean_gtav_title: 'Clean GTA V',
      confirm_clean_gtav_desc: 'Remove mod files from GTA V (official files are protected by the baseline)?',
      confirm_baseline_title: 'Create GTA V baseline',
      confirm_baseline_desc: 'Scans all official GTA V files (5–10 min). Run on a mod-free installation.',
      confirm_download_title: 'Download pack',
      confirm_download_desc: '« {name} » will be downloaded and extracted into your packs folder.',

      op_installing: 'Installing pack', op_uninstalling: 'Uninstalling',
      op_clean_fivem: 'Cleaning FiveM', op_clean_gtav: 'Cleaning GTA V',
      op_baseline: 'Creating GTA V baseline', op_downloading: 'Downloading pack',

      scanning: 'Scanning…', installing: 'Starting…', uninstalling: 'Deleting…',
      cleaning: 'Cleaning…', downloading: 'Downloading…', saving: 'Saving…',

      baseline_none: 'No baseline created',
      baseline_ok: 'Baseline present — {n} files indexed',
    },
  };

  let _locale = 'fr';
  let _dict   = LOCALES.fr;

  function t(key, vars) {
    let s = _dict[key] !== undefined ? _dict[key] : (LOCALES.en[key] || key);
    if (vars) {
      Object.entries(vars).forEach(([k, v]) => {
        s = s.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
      });
    }
    return s;
  }

  function apply() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      el.placeholder = t(el.dataset.i18nPh);
    });
  }

  function setLang(lang) {
    const l = SUPPORTED.includes(lang) ? lang : DEFAULT;
    _locale  = l;
    _dict    = LOCALES[l] || LOCALES[DEFAULT];
    apply();
    // Sync language select
    const sel = document.getElementById('lang-select');
    if (sel) sel.value = l;
    return l;
  }

  function init(savedLang) {
    const sys  = (navigator.language || 'fr').slice(0, 2).toLowerCase();
    const lang = savedLang || (SUPPORTED.includes(sys) ? sys : DEFAULT);
    return setLang(lang);
  }

  return { init, t, apply, setLang, locale: () => _locale, SUPPORTED };

})();
