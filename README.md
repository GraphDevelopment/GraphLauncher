# Graph Launcher

Gestionnaire de packs graphiques FiveM/GTA V avec interface moderne et sombre.

## Prérequis

- Python 3.12+
- Microsoft Edge WebView2 Runtime (inclus dans Windows 11, sinon [télécharger ici](https://developer.microsoft.com/en-us/microsoft-edge/webview2/))

## Installation rapide

```bash
pip install -r requirements.txt
python main.py
```

## Structure

```
├── main.py               # Point d'entrée
├── backend/
│   └── api.py            # Bridge Python ↔ JavaScript
├── core/
│   ├── pack_manager.py   # Scan, installation, désinstallation
│   ├── cleaner.py        # Nettoyage FiveM / GTA V
│   ├── backup.py         # Sauvegardes automatiques
│   └── baseline.py       # Protection SHA256 GTA V
├── services/
│   ├── file_service.py   # Opérations fichiers sécurisées
│   ├── validation_service.py
│   └── hash_service.py
├── database/
│   └── db_manager.py     # SQLite (settings, history, logs)
├── utils/
│   ├── logger.py
│   └── paths.py
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
├── build.py              # Script PyInstaller
└── installer.iss         # Inno Setup
```

## Logique d'installation des packs

| Dossier (insensible à la casse) | Destination |
|---|---|
| `mods/`         | FiveM Application Data/mods/ |
| `plugins/`      | FiveM Application Data/plugins/ |
| `citizen/`      | FiveM Application Data/citizen/ |
| `fivem/`        | FiveM Application Data/ (contenu) |
| `pack son/`, `audio/` | GTA V/x64/audio/sfx/ (fichiers .rpf seulement) |
| `gta5/`, `gta/` | GTA V/ (racine) |

## Build .exe

```bash
# Installer PyInstaller
pip install pyinstaller

# Construire
python build.py
```

L'exécutable sera dans `dist/FiveM_Graph_Launcher.exe`.

## Installateur Windows

Compilez `installer.iss` avec [Inno Setup 6](https://jrsoftware.org/isinfo.php) après le build PyInstaller.

## Sécurité

- Aucune opération sur des chemins système (`C:/Windows`, etc.)
- Protection baseline SHA256 pour GTA V
- Sauvegarde automatique avant chaque installation
- Confirmation utilisateur avant tout nettoyage
