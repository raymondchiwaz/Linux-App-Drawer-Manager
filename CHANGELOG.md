# Changelog

## Unreleased
### Added
- Show All / Custom toggle including system, Flatpak, and local applications.
- Search bar for filtering applications by name.
- Clone / Override & Edit functionality for system applications.
- Revert override action to remove local shadowing .desktop file.
- Hide (create `Hidden=true` override) and Unhide actions for system apps.
- Edit capability for all custom (and overridden) launchers.
- Support for script wrappers (Auto / Direct / python3 / bash / node / etc.).
- Extra arguments input, terminal toggle, mark-executable toggle.
- Absolute icon path handling with automatic copy into local icon theme.
- Duplicate detection by Exec command and sanitized name (opens existing instead of creating a new duplicate).
- Badges (OVERRIDE, HIDDEN) indicating override state and hidden entries.

### Changed
- Replaced deprecated dialog APIs with Gtk.Window based modals.
- Expanded list area to avoid cramped rows.
- Improved path quoting (handles spaces) for Exec commands.
- Override creation now appends custom marker if missing.

### Fixed
- Removed deprecated get_children() usage for ListBox (GTK4 compliant child removal).
- Fixed multiple syntax errors in f-strings for Terminal key generation.
- Ensured deletion confirmation works via custom confirmation window.
- Correct handling for icon copying and immediate availability.

### Known Issues / Future
- Deprecation warnings (Gtk.FileChooserNative, ComboBoxText) remain – planned migration to Gtk.FileDialog and Gtk.DropDown.
- No drag & drop yet (planned).
- No bulk operations yet.

### Notes
Visit https://rayistec.dev for updates and more projects.
