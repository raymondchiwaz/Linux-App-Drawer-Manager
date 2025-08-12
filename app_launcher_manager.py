#!/usr/bin/env python3
import gi, os, pathlib, subprocess, shutil, json, datetime, shlex
from typing import Optional

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gio, GLib, GObject, Adw

APP_ID = 'com.example.AppDrawerManager'
CUSTOM_MARKER_KEY = 'X-Custom-Added'
CUSTOM_MARKER_VALUE = '1'
LOCAL_APPS = pathlib.Path.home() / '.local/share/applications'

CSS = b"""
window, dialog { background-color: @theme_base_color; }
.list-row { padding: 6px; }
.success { color: green; }
.danger { color: #b00020; }
.warning { color: #c49000; }
.heading { font-weight: 600; font-size: 1.1em; }
"""

class DesktopEntry:
    def __init__(self, path: pathlib.Path):
        self.path = path
        self.data = self._parse()

    def _parse(self):
        d = {}
        try:
            with self.path.open('r', encoding='utf-8') as f:
                section = None
                for line in f:
                    line = line.strip('\n')
                    if not line or line.startswith('#'): continue
                    if line.startswith('[') and line.endswith(']'):
                        section = line[1:-1]
                        continue
                    if '=' in line and section == 'Desktop Entry':
                        k,v = line.split('=',1)
                        d[k.strip()] = v.strip()
        except Exception as e:
            print('Parse error', e)
        return d

    def is_custom(self):
        return self.data.get(CUSTOM_MARKER_KEY) == CUSTOM_MARKER_VALUE

    def display_name(self):
        return self.data.get('Name', self.path.name)

    def icon_name(self):
        return self.data.get('Icon')

class AppListRow(Adw.ActionRow):
    __gtype_name__ = 'AppListRow'
    def __init__(self, entry: DesktopEntry):
        super().__init__()
        self.entry = entry
        self.set_title(entry.display_name())
        if entry.icon_name():
            self.add_prefix(Gtk.Image.new_from_icon_name(entry.icon_name()))
        # Edit button
        edit_btn = Gtk.Button.new_from_icon_name('document-edit-symbolic')
        edit_btn.set_tooltip_text('Edit')
        edit_btn.connect('clicked', self.on_edit)
        self.add_suffix(edit_btn)
        # Remove button
        rm_btn = Gtk.Button.new_from_icon_name('user-trash-symbolic')
        rm_btn.add_css_class('destructive-action')
        rm_btn.set_tooltip_text('Delete')
        rm_btn.connect('clicked', self.on_remove)
        self.add_suffix(rm_btn)

    def on_edit(self, *_):
        parent_win = self.get_ancestor(AppWindow)
        if parent_win:
            EditDesktopWindow(parent_win, self.entry).present()

    def on_remove(self, *_):
        # Replace AlertDialog (was not functioning) with explicit confirmation window
        parent_win = self.get_ancestor(AppWindow)
        if not parent_win:
            return
        ConfirmDeleteWindow(parent_win, self.entry).present()

class AddDesktopWindow(Gtk.Window):
    def __init__(self, parent_win: 'AppWindow'):
        super().__init__(title='Create Launcher', transient_for=parent_win, modal=True)
        self.parent_win = parent_win
        self.set_default_size(520, 520)

        self.exec_path: Optional[str] = None

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        self.set_child(box)

        # Name
        self.name_entry = Gtk.Entry(placeholder_text='Application Name')
        # Comment
        self.comment_entry = Gtk.Entry(placeholder_text='Comment (optional)')
        # Exec chooser
        exec_box = Gtk.Box(spacing=6)
        self.exec_display = Gtk.Entry(editable=False, placeholder_text='No file selected')
        pick_exec_btn = Gtk.Button(label='Choose File')
        pick_exec_btn.connect('clicked', self.on_pick_exec)
        exec_box.append(self.exec_display)
        exec_box.append(pick_exec_btn)
        # Wrapper selection
        wrapper_label = Gtk.Label(label='Wrapper:', xalign=0)
        self.wrapper_combo = Gtk.ComboBoxText()
        for opt in ['Auto','Direct','python3','python','bash','sh','node']:
            self.wrapper_combo.append_text(opt)
        self.wrapper_combo.set_active(0)
        wrapper_box = Gtk.Box(spacing=6)
        wrapper_box.append(wrapper_label)
        wrapper_box.append(self.wrapper_combo)
        # Terminal toggle
        term_box = Gtk.Box(spacing=6)
        term_label = Gtk.Label(label='Run in Terminal:', xalign=0)
        self.terminal_switch = Gtk.Switch(active=False)
        term_box.append(term_label)
        term_box.append(self.terminal_switch)
        # Mark executable toggle
        exec_perm_box = Gtk.Box(spacing=6)
        exec_perm_label = Gtk.Label(label='Mark file executable:', xalign=0)
        self.exec_perm_switch = Gtk.Switch(active=True)
        exec_perm_box.append(exec_perm_label)
        exec_perm_box.append(self.exec_perm_switch)
        # Icon chooser
        icon_box = Gtk.Box(spacing=6)
        self.icon_entry = Gtk.Entry(placeholder_text='Icon name or file path')
        icon_btn = Gtk.Button(label='Browse Icon')
        icon_btn.connect('clicked', self.on_pick_icon)
        icon_box.append(self.icon_entry)
        icon_box.append(icon_btn)

        self.categories_entry = Gtk.Entry(placeholder_text='Categories (e.g. Utility;Development;)')
        self.args_entry = Gtk.Entry(placeholder_text='Extra arguments (optional)')

        action_box = Gtk.Box(spacing=6)
        close_btn = Gtk.Button(label='Close')
        close_btn.connect('clicked', lambda *_: self.close())
        create_btn = Gtk.Button(label='Create')
        create_btn.add_css_class('suggested-action')
        create_btn.connect('clicked', self.on_create)
        action_box.append(close_btn)
        action_box.append(create_btn)

        for w in [self.name_entry, self.comment_entry, exec_box, wrapper_box, term_box, exec_perm_box, self.args_entry, icon_box, self.categories_entry, action_box]:
            box.append(w)

    def on_pick_icon(self, *_):
        dialog = Gtk.FileChooserNative.new('Select Icon', self, Gtk.FileChooserAction.OPEN, 'Select', 'Cancel')
        flt = Gtk.FileFilter(); [flt.add_pattern(p) for p in ('*.png','*.svg','*.xpm')]; dialog.add_filter(flt)
        dialog.connect('response', lambda d,res: self.icon_entry.set_text(d.get_file().get_path()) if res == Gtk.ResponseType.ACCEPT else None)
        dialog.show()

    def on_pick_exec(self, *_):
        dialog = Gtk.FileChooserNative.new('Select File', self, Gtk.FileChooserAction.OPEN, 'Select', 'Cancel')
        dialog.connect('response', self._exec_chosen); dialog.show()

    def _exec_chosen(self, dialog, res):
        if res == Gtk.ResponseType.ACCEPT and (f := dialog.get_file()):
            self.exec_path = f.get_path()
            self.exec_display.set_text(self.exec_path)
            if not self.name_entry.get_text():
                stem = pathlib.Path(self.exec_path).stem.replace('_',' ').title()
                self.name_entry.set_text(stem)
            # Auto choose wrapper if extension suggests
            if self.wrapper_combo.get_active_text() == 'Auto':
                ext = pathlib.Path(self.exec_path).suffix.lower()
                if ext == '.py': self.wrapper_combo.set_active(self._wrapper_index('python3'))
                elif ext in ('.sh','.bash'): self.wrapper_combo.set_active(self._wrapper_index('bash'))
                elif ext == '.js': self.wrapper_combo.set_active(self._wrapper_index('node'))

    def _wrapper_index(self, name:str)->int:
        for i,opt in enumerate(['Auto','Direct','python3','python','bash','sh','node']):
            if opt == name: return i
        return 0

    def _build_exec_command(self)->str:
        if not self.exec_path:
            return ''
        wrapper = self.wrapper_combo.get_active_text() or 'Auto'
        path = self.exec_path
        raw_args = self.args_entry.get_text().strip()
        try:
            arg_tokens = shlex.split(raw_args) if raw_args else []
        except Exception:
            # fallback treat as single arg string
            arg_tokens = [raw_args] if raw_args else []
        parts: list[str] = []
        if wrapper == 'Auto':
            ext = pathlib.Path(path).suffix.lower()
            if os.access(path, os.X_OK) and ext not in ('.py','.sh','.bash','.js'):
                parts.append(path)
            elif ext == '.py':
                parts.extend(['python3', path])
            elif ext in ('.sh','.bash'):
                parts.extend(['bash', path])
            elif ext == '.js':
                parts.extend(['node', path])
            else:
                parts.append(path)
        elif wrapper == 'Direct':
            parts.append(path)
        else:
            parts.extend([wrapper, path])
        parts.extend(arg_tokens)
        return ' '.join(shlex.quote(p) for p in parts)

    def on_create(self, *_):
        if not self.exec_path:
            self._toast('Pick a file'); return
        name = self.name_entry.get_text().strip()
        if not name:
            self._toast('Name required'); return
        exec_cmd = self._build_exec_command()
        if not exec_cmd:
            self._toast('Exec could not be built'); return
        # possibly mark executable
        if self.exec_perm_switch.get_active():
            try: st = os.stat(self.exec_path); os.chmod(self.exec_path, st.st_mode | 0o111)
            except Exception: pass
        comment = self.comment_entry.get_text().strip()
        icon = self.icon_entry.get_text().strip()
        categories = self.categories_entry.get_text().strip()
        terminal = self.terminal_switch.get_active()
        fname = ''.join(c for c in name if c.isalnum() or c in ('-','_')).replace(' ','') or 'custom'
        desktop_path = LOCAL_APPS / f"{fname}.desktop"; counter = 1
        while desktop_path.exists():
            desktop_path = LOCAL_APPS / f"{fname}-{counter}.desktop"; counter += 1
        lines = [
            '[Desktop Entry]',
            f'Name={name}',
            'Type=Application',
            f'Exec={exec_cmd}',
            f'Terminal={"true" if terminal else "false"}'
        ]
        if comment: lines.append(f'Comment={comment}')
        if icon:
            if os.path.isfile(icon):
                target_dir = pathlib.Path.home()/'.local/share/icons/hicolor/128x128/apps'; target_dir.mkdir(parents=True, exist_ok=True)
                ext = pathlib.Path(icon).suffix or '.png'
                target_icon = target_dir / f"{fname}{ext}"
                try:
                    shutil.copyfile(icon, target_icon)
                    lines.append(f'Icon={target_icon}')  # use absolute path for immediate visibility
                except Exception:
                    lines.append(f'Icon={icon}')
            else:
                lines.append(f'Icon={icon}')
        if categories:
            if not categories.endswith(';'): categories += ';'
            lines.append(f'Categories={categories}')
        lines.append(f'{CUSTOM_MARKER_KEY}={CUSTOM_MARKER_VALUE}')
        try:
            LOCAL_APPS.mkdir(parents=True, exist_ok=True)
            desktop_path.write_text('\n'.join(lines)+'\n', encoding='utf-8')
            os.chmod(desktop_path, 0o644)
        except Exception as e:
            self._toast(f'Failed: {e}'); return
        self._toast('Created')
        self.parent_win.reload_list(); self.close()

    def _toast(self, msg):
        self.parent_win.toast_overlay.add_toast(Adw.Toast.new(msg))

class ImportDesktopWindow(Gtk.Window):
    def __init__(self, parent_win: 'AppWindow'):
        super().__init__(title='Import .desktop', transient_for=parent_win, modal=True)
        self.parent_win = parent_win
        self.set_default_size(360, 120)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        self.set_child(box)
        pick_btn = Gtk.Button(label='Choose .desktop File'); pick_btn.connect('clicked', self.on_pick)
        close_btn = Gtk.Button(label='Close'); close_btn.connect('clicked', lambda *_: self.close())
        hb = Gtk.Box(spacing=6); hb.append(pick_btn); hb.append(close_btn)
        box.append(Gtk.Label(label='Import an existing .desktop launcher into your local applications.'))
        box.append(hb)

    def on_pick(self, *_):
        dialog = Gtk.FileChooserNative.new('Select .desktop', self, Gtk.FileChooserAction.OPEN, 'Select', 'Cancel')
        flt = Gtk.FileFilter(); flt.add_pattern('*.desktop'); dialog.add_filter(flt)
        dialog.connect('response', self._chosen); dialog.show()

    def _chosen(self, dialog, res):
        if res == Gtk.ResponseType.ACCEPT and (f := dialog.get_file()):
            path = pathlib.Path(f.get_path())
            try:
                contents = path.read_text(encoding='utf-8')
                if f'{CUSTOM_MARKER_KEY}=' not in contents:
                    contents += f'\n{CUSTOM_MARKER_KEY}={CUSTOM_MARKER_VALUE}\n'
                target = LOCAL_APPS / path.name
                if target.exists():
                    target = LOCAL_APPS / f"imported-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{path.name}"
                target.write_text(contents, encoding='utf-8')
                self.parent_win.reload_list()
                self.parent_win.toast_overlay.add_toast(Adw.Toast.new('Imported'))
            except Exception as e:
                self.parent_win.toast_overlay.add_toast(Adw.Toast.new(f'Import failed: {e}'))
        self.close()

class EditDesktopWindow(Gtk.Window):
    def __init__(self, parent_win: 'AppWindow', desktop_entry: DesktopEntry):
        super().__init__(title='Edit Launcher', transient_for=parent_win, modal=True)
        self.parent_win = parent_win
        self.entry = desktop_entry
        self.set_default_size(520, 520)
        self.original_path = desktop_entry.path
        self.data = dict(desktop_entry.data)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        self.set_child(box)

        self.name_entry = Gtk.Entry(text=self.data.get('Name',''), placeholder_text='Application Name')
        self.comment_entry = Gtk.Entry(text=self.data.get('Comment',''), placeholder_text='Comment (optional)')
        self.exec_entry = Gtk.Entry(text=self.data.get('Exec',''), placeholder_text='Exec command')

        terminal_val = self.data.get('Terminal','false').lower() == 'true'
        term_box = Gtk.Box(spacing=6)
        term_label = Gtk.Label(label='Run in Terminal:', xalign=0)
        self.terminal_switch = Gtk.Switch(active=terminal_val)
        term_box.append(term_label)
        term_box.append(self.terminal_switch)

        icon_box = Gtk.Box(spacing=6)
        self.icon_entry = Gtk.Entry(text=self.data.get('Icon',''), placeholder_text='Icon name or file path')
        icon_btn = Gtk.Button(label='Browse Icon')
        icon_btn.connect('clicked', self.on_pick_icon)
        icon_box.append(self.icon_entry)
        icon_box.append(icon_btn)

        self.categories_entry = Gtk.Entry(text=self.data.get('Categories',''), placeholder_text='Categories (e.g. Utility;Development;)')

        choose_exec_btn = Gtk.Button(label='Browse File')
        choose_exec_btn.connect('clicked', self.on_pick_exec)

        action_box = Gtk.Box(spacing=6)
        cancel_btn = Gtk.Button(label='Cancel')
        cancel_btn.connect('clicked', lambda *_: self.close())
        save_btn = Gtk.Button(label='Save')
        save_btn.add_css_class('suggested-action')
        save_btn.connect('clicked', self.on_save)
        action_box.append(cancel_btn)
        action_box.append(save_btn)

        for w in [self.name_entry, self.comment_entry, self.exec_entry, choose_exec_btn, term_box, icon_box, self.categories_entry, action_box]:
            box.append(w)

    def on_pick_icon(self, *_):
        dialog = Gtk.FileChooserNative.new('Select Icon', self, Gtk.FileChooserAction.OPEN, 'Select', 'Cancel')
        flt = Gtk.FileFilter(); [flt.add_pattern(p) for p in ('*.png','*.svg','*.xpm')]; dialog.add_filter(flt)
        dialog.connect('response', lambda d,res: self.icon_entry.set_text(d.get_file().get_path()) if res == Gtk.ResponseType.ACCEPT else None)
        dialog.show()

    def on_pick_exec(self, *_):
        dialog = Gtk.FileChooserNative.new('Select File', self, Gtk.FileChooserAction.OPEN, 'Select', 'Cancel')
        dialog.connect('response', self._exec_chosen); dialog.show()

    def _exec_chosen(self, dialog, res):
        if res == Gtk.ResponseType.ACCEPT and (f := dialog.get_file()):
            self.exec_entry.set_text(f.get_path())

    def on_save(self, *_):
        name = self.name_entry.get_text().strip(); exec_cmd = self.exec_entry.get_text().strip(); comment = self.comment_entry.get_text().strip(); icon = self.icon_entry.get_text().strip(); categories = self.categories_entry.get_text().strip(); terminal = self.terminal_switch.get_active()
        if not name or not exec_cmd: self._toast('Name and Exec required'); return
        try:
            lines = ['[Desktop Entry]', f'Name={name}', 'Type=Application', f'Exec={exec_cmd}', f'Terminal={"true" if terminal else "false"}']
            if comment: lines.append(f'Comment={comment}')
            if icon:
                if os.path.isfile(icon):
                    # If pointing to a file, ensure it is staged inside icon theme for consistency, but still use absolute path
                    fname = ''.join(c for c in name if c.isalnum() or c in ('-','_')) or 'custom'
                    target_dir = pathlib.Path.home()/'.local/share/icons/hicolor/128x128/apps'; target_dir.mkdir(parents=True, exist_ok=True)
                    ext = pathlib.Path(icon).suffix or '.png'
                    target_icon = target_dir / f"{fname}{ext}"
                    try:
                        if pathlib.Path(icon) != target_icon:
                            shutil.copyfile(icon, target_icon)
                        lines.append(f'Icon={target_icon}')
                    except Exception:
                        lines.append(f'Icon={icon}')
                else:
                    lines.append(f'Icon={icon}')
            if categories:
                if not categories.endswith(';'): categories += ';'
                lines.append(f'Categories={categories}')
            if CUSTOM_MARKER_KEY not in self.data: lines.append(f'{CUSTOM_MARKER_KEY}={CUSTOM_MARKER_VALUE}')
            self.original_path.write_text('\n'.join(lines)+'\n', encoding='utf-8')
        except Exception as e:
            self._toast(f'Failed: {e}'); return
        self.parent_win.reload_list(); self._toast('Saved'); self.close()

    def _toast(self, msg):
        self.parent_win.toast_overlay.add_toast(Adw.Toast.new(msg))

class ConfirmDeleteWindow(Gtk.Window):
    def __init__(self, parent_win: 'AppWindow', entry: DesktopEntry):
        super().__init__(title='Delete Launcher', transient_for=parent_win, modal=True)
        self.parent_win = parent_win
        self.entry = entry
        self.set_default_size(360, 140)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
        self.set_child(box)
        box.append(Gtk.Label(label=f"Remove '{entry.display_name()}'? This deletes the .desktop file.", wrap=True, xalign=0))
        btn_box = Gtk.Box(spacing=6)
        cancel_btn = Gtk.Button(label='Cancel'); cancel_btn.connect('clicked', lambda *_: self.close())
        delete_btn = Gtk.Button(label='Delete'); delete_btn.add_css_class('destructive-action'); delete_btn.connect('clicked', self._do_delete)
        btn_box.append(cancel_btn); btn_box.append(delete_btn)
        box.append(btn_box)

    def _do_delete(self, *_):
        try:
            if self.entry.path.exists():
                self.entry.path.unlink()
                self.parent_win.toast_overlay.add_toast(Adw.Toast.new('Deleted'))
        except Exception as e:
            self.parent_win.toast_overlay.add_toast(Adw.Toast.new(f'Failed: {e}'))
        self.parent_win.reload_list()
        self.close()

class AppWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title('App Drawer Manager')
        self.set_default_size(640, 520)

        self.toast_overlay = Adw.ToastOverlay(); self.set_content(self.toast_overlay)

        clamp = Adw.Clamp(maximum_size=800); self.toast_overlay.set_child(clamp)
        clamp.set_hexpand(True); clamp.set_vexpand(True)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.set_hexpand(True); vbox.set_vexpand(True)
        clamp.set_child(vbox)

        header = Adw.HeaderBar(); vbox.append(header)

        add_btn = Gtk.Button.new_from_icon_name('list-add-symbolic'); add_btn.set_tooltip_text('Create from executable'); add_btn.connect('clicked', lambda *_: AddDesktopWindow(self).present())
        import_btn = Gtk.Button.new_from_icon_name('document-open-symbolic'); import_btn.set_tooltip_text('Import existing .desktop'); import_btn.connect('clicked', lambda *_: ImportDesktopWindow(self).present())
        header.pack_start(add_btn); header.pack_start(import_btn)

        self.status_label = Gtk.Label(label=''); header.set_title_widget(self.status_label)

        self.list_box = Gtk.ListBox(); self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.set_vexpand(True); self.list_box.set_hexpand(True)

        scroller = Gtk.ScrolledWindow(); scroller.set_child(self.list_box)
        scroller.set_hexpand(True); scroller.set_vexpand(True)
        vbox.append(scroller)

        self.reload_list()

    def reload_list(self):
        # Clear existing children (GTK4 removed get_children())
        child = self.list_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.list_box.remove(child)
            child = next_child
        entries = []
        if LOCAL_APPS.exists():
            for p in LOCAL_APPS.glob('*.desktop'):
                entry = DesktopEntry(p)
                if entry.is_custom():
                    entries.append(entry)
        entries.sort(key=lambda e: e.display_name().lower())
        for e in entries:
            self.list_box.append(AppListRow(e))
        self.status_label.set_text(f'Custom Launchers: {len(entries)}')

class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        win = self.props.active_window
        if not win:
            win = AppWindow(self)
        win.present()

def ensure_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS)
    display = Gdk.Display.get_default() if hasattr(Gtk, 'Display') else None
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
    )

if __name__ == '__main__':
    # Avoid importing Gdk earlier if not needed
    gi.require_version('Gdk', '4.0')
    from gi.repository import Gdk
    # Apply CSS
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
    )
    app = App()
    app.run()
