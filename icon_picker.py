#!/usr/bin/env python3
import gi
import subprocess
import threading  # Added for background loading

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib  # Added GLib for UI thread communication


class IconPicker(Adw.Window):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_default_size(1100, 800)
        self.set_title("Icon Picker")

        self.icon_theme = Gtk.IconTheme.get_for_display(self.get_display())
        self.selected_icon_name = None
        self.selected_icon_path = None
        self.filters = {}

        # The main stack now handles the transition from Loading -> Main UI
        self.main_stack = Gtk.Stack()
        self.main_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        self.view_stack = Adw.ViewStack()
        self.view_stack.set_vexpand(True)

        self._build_loading_ui()
        self._build_ui()

        self.set_content(self.main_stack)

        # Start loading in the background
        threading.Thread(target=self._load_data_async, daemon=True).start()

    def _build_loading_ui(self):
        """Creates a splash/loading screen."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        icon = Gtk.Image.new_from_icon_name("io.github.killown.icon_picker")
        icon.set_pixel_size(128)

        spinner = Gtk.Spinner()
        spinner.start()
        spinner.set_size_request(32, 32)

        label = Gtk.Label(label="Indexing system icons...")
        label.add_css_class("title-1")

        box.append(icon)
        box.append(label)
        box.append(spinner)

        self.main_stack.add_named(box, "loading")

    def _load_data_async(self):
        """Heavy lifting done in a background thread."""
        icon_sets = self._get_icon_data()
        # Schedule the UI update on the main thread
        GLib.idle_add(self._on_data_loaded, icon_sets)

    def _on_data_loaded(self, icon_sets):
        """Switch from splash screen to the main app."""
        self._populate_categories(icon_sets)
        self.main_stack.set_visible_child_name("main")

    def _get_icon_data(self):
        data = {
            "All": Gtk.StringList(),
            "Applications": Gtk.StringList(),
            "Places": Gtk.StringList(),
            "Devices": Gtk.StringList(),
            "Status": Gtk.StringList(),
            "Symbolic": Gtk.StringList(),
        }

        all_icons = self.icon_theme.get_icon_names()
        for name in sorted(all_icons):
            data["All"].append(name)
            if name.endswith("-symbolic"):
                data["Symbolic"].append(name)
                continue

            paintable = self.icon_theme.lookup_icon(name, None, 48, 1, 0, 0)
            if (
                paintable
                and (file := paintable.get_file())
                and (path := file.get_path())
            ):
                path_lower = path.lower()
                if "/apps/" in path_lower or "/applications/" in path_lower:
                    data["Applications"].append(name)
                elif "/places/" in path_lower:
                    data["Places"].append(name)
                elif "/devices/" in path_lower:
                    data["Devices"].append(name)
                elif "/status/" in path_lower or "/panel/" in path_lower:
                    data["Status"].append(name)
        return data

    def _populate_categories(self, icon_sets):
        sections = [
            ("All", "All Icons", "Every icon in the theme", "view-grid-symbolic"),
            (
                "Applications",
                "Applications",
                "Apps and binaries",
                "application-x-executable-symbolic",
            ),
            ("Places", "Places", "Folders and locations", "folder-symbolic"),
            ("Devices", "Devices", "Hardware and drives", "drive-harddisk-symbolic"),
            ("Status", "Status", "System indicators", "dialog-information-symbolic"),
            ("Symbolic", "Symbolic", "Interface symbols", "view-filter-symbolic"),
        ]

        for context_key, label, subtitle, icon_name in sections:
            base_model = icon_sets[context_key]
            if base_model.get_n_items() == 0:
                continue

            filter_obj = Gtk.StringFilter(
                expression=Gtk.PropertyExpression.new(Gtk.StringObject, None, "string")
            )
            filter_obj.set_match_mode(Gtk.StringFilterMatchMode.SUBSTRING)
            filter_model = Gtk.FilterListModel(model=base_model, filter=filter_obj)
            self.filters[context_key.lower()] = filter_obj

            grid = self._create_icon_grid(filter_model)
            self.view_stack.add_titled(grid, context_key.lower(), label)

            row = Adw.ActionRow(title=label, subtitle=subtitle)
            row_icon = Gtk.Image.new_from_icon_name(icon_name)
            row_icon.set_pixel_size(32)
            row.add_prefix(row_icon)
            row.set_metadata(context_key.lower())
            self.sidebar_list.append(row)

        first_row = self.sidebar_list.get_row_at_index(0)
        if first_row:
            self.sidebar_list.select_row(first_row)

    def _create_icon_grid(self, model):
        scrolled = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)
        selection = Gtk.SingleSelection(model=model)
        selection.connect("selection-changed", self._on_selection_changed)
        grid_view = Gtk.GridView(
            model=selection, factory=factory, max_columns=12, min_columns=4
        )
        grid_view.set_vexpand(True)
        scrolled.set_child(grid_view)
        return scrolled

    def _on_factory_setup(self, f, li):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_end(12)
        img = Gtk.Image(pixel_size=48)
        lbl = Gtk.Label(ellipsize=3, max_width_chars=14)
        box.append(img)
        box.append(lbl)
        li.set_child(box)

    def _on_factory_bind(self, f, li):
        if (box := li.get_child()) and (item := li.get_item()):
            img = box.get_first_child()
            lbl = img.get_next_sibling()
            name = item.get_string()
            img.set_from_icon_name(name)
            lbl.set_label(name)

    def _on_selection_changed(self, selection, position, n_items):
        item = selection.get_selected_item()
        if item:
            self.selected_icon_name = item.get_string()
            paintable = self.icon_theme.lookup_icon(
                self.selected_icon_name, None, 256, 1, 0, 0
            )
            if paintable and (file := paintable.get_file()):
                self.selected_icon_path = file.get_path()
            self.copy_name_btn.set_sensitive(True)
            self.copy_path_btn.set_sensitive(True)
            self.copy_img_btn.set_sensitive(True)

    def _on_search_changed(self, entry):
        text = entry.get_text()
        current_cat = self.view_stack.get_visible_child_name()
        if current_cat in self.filters:
            self.filters[current_cat].set_search(text)

    def _on_copy_clicked(self, btn, mode):
        if mode == "img" and self.selected_icon_path:
            try:
                with open(self.selected_icon_path, "rb") as f:
                    subprocess.run(["wl-copy"], input=f.read(), check=True)
                self.toast_overlay.add_toast(
                    Adw.Toast(title="Image copied to clipboard")
                )
            except Exception as e:
                self.toast_overlay.add_toast(Adw.Toast(title=f"Error: {str(e)}"))
            return
        clipboard = self.get_display().get_clipboard()
        text = self.selected_icon_name if mode == "name" else self.selected_icon_path
        if text:
            clipboard.set(text)
            self.toast_overlay.add_toast(Adw.Toast(title=f"Copied {mode}"))

    def _build_ui(self):
        self.toast_overlay = Adw.ToastOverlay()
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        header = Adw.HeaderBar()
        self.search_entry = Gtk.SearchEntry(placeholder_text="Filter icon names...")
        self.search_entry.connect("search-changed", self._on_search_changed)
        header.set_title_widget(self.search_entry)

        self.copy_name_btn = Gtk.Button(label="Name", sensitive=False)
        self.copy_name_btn.connect("clicked", self._on_copy_clicked, "name")
        header.pack_end(self.copy_name_btn)

        self.copy_path_btn = Gtk.Button(label="Path", sensitive=False)
        self.copy_path_btn.connect("clicked", self._on_copy_clicked, "path")
        header.pack_end(self.copy_path_btn)

        self.copy_img_btn = Gtk.Button(label="Copy Image", sensitive=False)
        self.copy_img_btn.add_css_class("suggested-action")
        self.copy_img_btn.connect("clicked", self._on_copy_clicked, "img")
        header.pack_end(self.copy_img_btn)

        main_box.append(header)
        split_view = Adw.NavigationSplitView(vexpand=True)

        sidebar_page = Adw.NavigationPage(title="Categories")
        self.sidebar_list = Gtk.ListBox()
        self.sidebar_list.add_css_class("navigation-sidebar")
        self.sidebar_list.connect(
            "row-selected",
            lambda lb, row: self.view_stack.set_visible_child_name(row.get_metadata())
            if row
            else None,
        )

        sw = Gtk.ScrolledWindow()
        sw.set_child(self.sidebar_list)
        sidebar_page.set_child(sw)

        content_page = Adw.NavigationPage(title="Icons")
        content_page.set_child(self.view_stack)

        split_view.set_sidebar(sidebar_page)
        split_view.set_content(content_page)
        main_box.append(split_view)

        self.toast_overlay.set_child(main_box)
        self.main_stack.add_named(self.toast_overlay, "main")


# Metadata helpers
Adw.ActionRow.set_metadata = lambda self, d: setattr(self, "_metadata", d)
Adw.ActionRow.get_metadata = lambda self: getattr(self, "_metadata", None)

if __name__ == "__main__":
    app = Adw.Application(application_id="io.github.killown.icon_picker")
    app.connect("activate", lambda a: IconPicker(application=a).present())
    app.run(None)
