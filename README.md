![Icon Picker Logo](io.github.killown.icon_picker.svg)

# Icon Picker

A modern GTK4/Libadwaita utility to browse and copy system icons.

AGPL-3.0 License

## Features

- **Category Filtering:** Automatically sorts icons into Applications, Places, Devices, and Status.
- **Asynchronous Loading:** Features a splash screen while indexing thousands of system icons to keep the UI responsive.
- **One-Click Export:** Copy icon names, system paths, or raw image data directly to your clipboard.
- **Flatpak Ready:** Fully sandboxed and compatible with modern Linux distributions.

## Folder Structure

For Flatpak development, ensure your repository follows this structure:

icon_picker/
├── io.github.killown.icon_picker.yml # Build Manifest
├── io.github.killown.icon_picker.desktop # Desktop Entry
├── io.github.killown.icon_picker.svg # App Icon
├── icon_picker.py # Python Source
└── LICENSE # AGPLv3 Text

## Installation (Flatpak)

To build and install the application locally using `flatpak-builder`:

\# 1. Install GNOME SDK
flatpak install flathub org.gnome.Sdk//47 org.gnome.Platform//47

# 2. Build and Install

flatpak-builder --user --install --force-clean build-dir io.github.killown.icon_picker.yml

# 3. Run

flatpak run io.github.killown.icon_picker

## Technical Permissions

This application requires the following sandbox permissions defined in the manifest:

- `wayland/x11`: Windowing system access.
- `xdg-data/icons:ro`: Read-only access to system icon themes.
- `own-name`: D-Bus registration for `io.github.killown.icon_picker`.

Copyright © 2025 Thiago Lucio. Provided under the [GNU Affero General Public License v3](./LICENSE).
