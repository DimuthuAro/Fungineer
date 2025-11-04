import pygame as pg
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox, simpledialog
from PIL import Image, ImageTk
import os

class SpriteManagerGUI:
    def __init__(self, sprite_manager):
        self.sprite_manager = sprite_manager
        self.root = tk.Tk()
        self.root.title("Sprite Manager")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Selected sprite tracking
        self.selected_sprite = None
        self.zoom_level = 1.0
        
        # Canvas panning variables
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.is_panning = False
        
        # View mode (list or thumbnail)
        self.view_mode = tk.StringVar(value="list")
        self.thumbnail_size = 80
        self.thumbnail_cache = {}
        
        # Initialize pygame if not already done
        if not pg.get_init():
            pg.init()
        
        # Set up close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
        self.refresh_sprite_list()
        self.root.mainloop()
    
    def setup_ui(self):
        """Setup the main UI layout"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        # Keep a reference to adjust layout dynamically based on view mode
        self.main_frame = main_frame
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        # Default to equal columns; will adjust when switching to thumbnail view
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        # Ensure both the top rows (0 and 1) can expand so left and right panes share height
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Left Panel - Sprite List
        self.setup_sprite_list_panel(main_frame)
        
        # Right Panel - Sprite Preview and Tools
        self.setup_preview_panel(main_frame)
        
        # Bottom Panel - Actions
        self.setup_action_panel(main_frame)
        # Apply initial layout sizing for the current view mode
        self.update_layout_for_view_mode()
    
    def setup_sprite_list_panel(self, parent):
        """Setup left panel with sprite list"""
        list_frame = ttk.LabelFrame(parent, text="Sprites", padding="5")
        list_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 5))
        
        # Top toolbar with search and view toggle
        toolbar_frame = ttk.Frame(list_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Search bar
        search_frame = ttk.Frame(toolbar_frame)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_sprite_list())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # View mode toggle buttons
        view_frame = ttk.Frame(toolbar_frame)
        view_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Radiobutton(view_frame, text="List", variable=self.view_mode, value="list", 
                       command=self.switch_view_mode).pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(view_frame, text="Icons", variable=self.view_mode, value="thumbnail", 
                       command=self.switch_view_mode).pack(side=tk.LEFT, padx=2)
        
        # Container for both list and thumbnail views
        self.view_container = ttk.Frame(list_frame)
        self.view_container.pack(fill=tk.BOTH, expand=True)
        
        # List view (original listbox)
        self.list_view_frame = ttk.Frame(self.view_container)
        
        list_scrollbar = ttk.Scrollbar(self.list_view_frame)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.sprite_listbox = tk.Listbox(self.list_view_frame, yscrollcommand=list_scrollbar.set, width=30, selectmode=tk.EXTENDED)
        self.sprite_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sprite_listbox.bind('<<ListboxSelect>>', self.on_sprite_select)
        
        list_scrollbar.config(command=self.sprite_listbox.yview)
        
        # Bind delete key to root window with focus check
        self.root.bind('<Delete>', lambda e: self.delete_sprite())
        self.root.bind('<BackSpace>', lambda e: self.delete_sprite())  # Also support backspace
        
        # Other HotKeys
        self.root.bind('<Control-n>', lambda e: self.create_sprite())
        self.root.bind('<Control-d>', lambda e: self.duplicate_sprite())
        self.root.bind('<Control-r>', lambda e: self.rename_sprite())
        self.root.bind('<F2>', lambda e: self.rename_sprite())
        self.root.bind('<Control-e>', lambda e: self.export_sprite())
        
        # Thumbnail view (canvas with grid)
        self.thumbnail_view_frame = ttk.Frame(self.view_container)
        
        thumb_scrollbar_v = ttk.Scrollbar(self.thumbnail_view_frame, orient=tk.VERTICAL)
        thumb_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        
        thumb_scrollbar_h = ttk.Scrollbar(self.thumbnail_view_frame, orient=tk.HORIZONTAL)
        thumb_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.thumbnail_canvas = tk.Canvas(self.thumbnail_view_frame, bg='#404040', 
                                         yscrollcommand=thumb_scrollbar_v.set,
                                         xscrollcommand=thumb_scrollbar_h.set,
                                         highlightthickness=0)
        self.thumbnail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        thumb_scrollbar_v.config(command=self.thumbnail_canvas.yview)
        thumb_scrollbar_h.config(command=self.thumbnail_canvas.xview)
        
        self.thumbnail_canvas.bind('<Button-1>', self.on_thumbnail_click)
        self.thumbnail_canvas.bind('<Control-Button-1>', self.on_thumbnail_ctrl_click)
        self.thumbnail_canvas.bind('<MouseWheel>', lambda e: self.thumbnail_canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        # Bind events to thumbnail canvas instead of container
        self.thumbnail_canvas.bind('<Configure>', lambda e: self.refresh_thumbnails())
        # Store thumbnail items data
        self.thumbnail_items = {}
        self.selected_thumbnails = set()
        
        # Show list view by default
        self.list_view_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sprite count label
        self.count_label = ttk.Label(list_frame, text="Total sprites: 0")
        self.count_label.pack(pady=(5, 0))
        
        
    
    def setup_preview_panel(self, parent):
        """Setup right panel with sprite preview"""
        preview_frame = ttk.LabelFrame(parent, text="Preview", padding="5")
        # Span two rows so preview panel height matches list view (which spans two rows)
        preview_frame.grid(row=0, column=1, rowspan=2, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)
        
        # Info bar
        info_frame = ttk.Frame(preview_frame)
        info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        self.info_label = ttk.Label(info_frame, text="No sprite selected")
        self.info_label.pack(side=tk.LEFT)
        
        # Zoom controls
        zoom_frame = ttk.Frame(info_frame)
        zoom_frame.pack(side=tk.RIGHT)
        
        ttk.Button(zoom_frame, text="-", width=3, command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        self.zoom_label = ttk.Label(zoom_frame, text="100%", width=6)
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="+", width=3, command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Reset", command=self.zoom_reset).pack(side=tk.LEFT, padx=2)
        
        # Canvas for sprite preview
        canvas_frame = ttk.Frame(preview_frame, relief=tk.SUNKEN, borderwidth=2)
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        
        self.preview_canvas = tk.Canvas(canvas_frame, bg='#808080', highlightthickness=0)
                
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events
        self.preview_canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        # Left mouse button drag for panning
        self.preview_canvas.bind("<ButtonPress-1>", self.start_pan)
        self.preview_canvas.bind("<B1-Motion>", self.do_pan)
        self.preview_canvas.bind("<ButtonRelease-1>", self.end_pan)

    def on_preview_canvas_resize(self, event):
        """Handle preview canvas resize without causing geometry loops."""
        # Debounce rapid configure events
        if hasattr(self, "_resize_after_id") and self._resize_after_id:
            try:
                self.preview_canvas.after_cancel(self._resize_after_id)
            except Exception:
                pass
        # Schedule a redraw shortly after resizing settles
        self._resize_after_id = self.preview_canvas.after(50, self.display_sprite)
        
    
    def setup_action_panel(self, parent):
        """Setup bottom panel with action buttons"""
        action_frame = ttk.LabelFrame(parent, text="Actions", padding="5")
        action_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        # File operations
        file_frame = ttk.LabelFrame(action_frame, text="File Operations")
        file_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        ttk.Button(file_frame, text="Load Sprite", command=self.load_sprite).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Load Multiple", command=self.load_multiple_sprites).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Load Spritesheet", command=self.load_spritesheet).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Export Sprite", command=self.export_sprite).pack(fill=tk.X, pady=2)
        ttk.Button(file_frame, text="Export All", command=self.export_all_sprites).pack(fill=tk.X, pady=2)
        
        # Create operations
        create_frame = ttk.LabelFrame(action_frame, text="Create")
        create_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        ttk.Button(create_frame, text="New Sprite", command=self.create_sprite).pack(fill=tk.X, pady=2)
        ttk.Button(create_frame, text="Duplicate", command=self.duplicate_sprite).pack(fill=tk.X, pady=2)
        
        # Edit operations
        edit_frame = ttk.LabelFrame(action_frame, text="Edit")
        edit_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        ttk.Button(edit_frame, text="Rename", command=self.rename_sprite).pack(fill=tk.X, pady=2)
        ttk.Button(edit_frame, text="Resize", command=self.resize_sprite).pack(fill=tk.X, pady=2)
        ttk.Button(edit_frame, text="Crop", command=self.crop_sprite).pack(fill=tk.X, pady=2)
        ttk.Button(edit_frame, text="Split Sprite", command=self.split_sprite).pack(fill=tk.X, pady=2)
        ttk.Button(edit_frame, text="Split by Transparency", command=self.split_by_transparency).pack(fill=tk.X, pady=2)
        ttk.Button(edit_frame, text="Paint/Draw", command=self.paint_sprite).pack(fill=tk.X, pady=2)
        ttk.Button(edit_frame, text="Brightness/Contrast", command=self.adjust_sprite).pack(fill=tk.X, pady=2)
        ttk.Button(edit_frame, text="Flip H", command=self.flip_sprite_horizontal).pack(fill=tk.X, pady=2)
        ttk.Button(edit_frame, text="Flip V", command=self.flip_sprite_vertical).pack(fill=tk.X, pady=2)
        ttk.Button(edit_frame, text="Rotate", command=self.rotate_sprite).pack(fill=tk.X, pady=2)
        ttk.Button(edit_frame, text="Delete", command=self.delete_sprite).pack(fill=tk.X, pady=2)
        
        # Utility operations
        util_frame = ttk.LabelFrame(action_frame, text="Utilities")
        util_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        ttk.Button(util_frame, text="Clear All", command=self.clear_all_sprites).pack(fill=tk.X, pady=2)
        ttk.Button(util_frame, text="Refresh", command=self.refresh_sprite_list).pack(fill=tk.X, pady=2)

    def flip_sprite_horizontal(self):
        """Flip selected sprite horizontally"""
        if not self.selected_sprite:
            messagebox.showwarning("Warning", "No sprite selected")
            return
        
        sprite = self.sprite_manager.get_sprite(self.selected_sprite)
        if sprite:
            flipped_sprite = pg.transform.flip(sprite, True, False)
            self.sprite_manager.add_sprite(self.selected_sprite, flipped_sprite)
            self.display_sprite()

    def flip_sprite_vertical(self):
        """Flip selected sprite vertically"""
        if not self.selected_sprite:
            messagebox.showwarning("Warning", "No sprite selected")
            return

        sprite = self.sprite_manager.get_sprite(self.selected_sprite)
        if sprite:
            flipped_sprite = pg.transform.flip(sprite, False, True)
            self.sprite_manager.add_sprite(self.selected_sprite, flipped_sprite)
            self.display_sprite()

    def switch_view_mode(self):
        """Switch between list and thumbnail view"""
        mode = self.view_mode.get()
        
        # Hide both views
        self.list_view_frame.pack_forget()
        self.thumbnail_view_frame.pack_forget()
        
        # Show selected view
        if mode == "list":
            self.list_view_frame.pack(fill=tk.BOTH, expand=True)
        else:
            self.thumbnail_view_frame.pack(fill=tk.BOTH, expand=True)
            self.refresh_thumbnails()
        # Adjust layout ratio based on selected mode
        self.update_layout_for_view_mode()

    def update_layout_for_view_mode(self):
        """Make preview panel wider when in thumbnail view (3x left panel)."""
        try:
            mode = self.view_mode.get()
        except Exception:
            mode = "list"
        if mode == "thumbnail":
            # Left panel weight 1, right (preview) weight 3
            self.main_frame.columnconfigure(0, weight=1)
            self.main_frame.columnconfigure(1, weight=3)
        else:
            # Equal widths in list mode
            self.main_frame.columnconfigure(0, weight=1)
            self.main_frame.columnconfigure(1, weight=1)
    
    def refresh_sprite_list(self):
        """Refresh the sprite list from sprite manager"""
        self.sprite_listbox.delete(0, tk.END)
        for name in sorted(self.sprite_manager.sprites.keys()):
            self.sprite_listbox.insert(tk.END, name)
        self.count_label.config(text=f"Total sprites: {len(self.sprite_manager.sprites)}")
        
        # Also refresh thumbnails if in thumbnail view
        if self.view_mode.get() == "thumbnail":
            self.refresh_thumbnails()
    
    def filter_sprite_list(self):
        """Filter sprite list based on search query"""
        search_term = self.search_var.get().lower()
        self.sprite_listbox.delete(0, tk.END)
        
        for name in sorted(self.sprite_manager.sprites.keys()):
            if search_term in name.lower():
                self.sprite_listbox.insert(tk.END, name)
        
        # Also filter thumbnails if in thumbnail view
        if self.view_mode.get() == "thumbnail":
            self.refresh_thumbnails()
    
    def refresh_thumbnails(self):
        """Refresh thumbnail grid view"""
        self.thumbnail_canvas.delete("all")
        self.thumbnail_items.clear()
        self.thumbnail_cache.clear()
        self.selected_thumbnails.clear()
        
        search_term = self.search_var.get().lower()
        filtered_sprites = [(name, sprite) for name, sprite in sorted(self.sprite_manager.sprites.items()) 
                           if search_term in name.lower()]
        
        if not filtered_sprites:
            return
        
        # Calculate grid layout
        canvas_width = self.thumbnail_canvas.winfo_width()
        if canvas_width < 50:
            canvas_width = 300  # Default width
        
        padding = 10
        thumb_total_size = self.thumbnail_size + padding
        cols = max(1, (canvas_width - padding) // thumb_total_size)
        
        # Create thumbnails
        row = 0
        col = 0
        for name, sprite in filtered_sprites:
            x = padding + col * thumb_total_size
            y = padding + row * thumb_total_size
            
            # Create thumbnail image
            try:
                sprite_string = pg.image.tostring(sprite, 'RGBA')
                pil_image = Image.frombytes('RGBA', sprite.get_size(), sprite_string)
                
                # Calculate thumbnail size maintaining aspect ratio
                width, height = sprite.get_size()
                ratio = min(self.thumbnail_size / width, self.thumbnail_size / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.NEAREST)
                thumb_photo = ImageTk.PhotoImage(pil_image)
                
                # Store reference to prevent garbage collection
                self.thumbnail_cache[name] = thumb_photo
                
                # Draw background
                bg_id = self.thumbnail_canvas.create_rectangle(
                    x, y, x + self.thumbnail_size, y + self.thumbnail_size,
                    fill='#505050', outline='#707070', width=2, tags=(name, 'bg')
                )
                
                # Draw thumbnail centered
                img_x = x + self.thumbnail_size // 2
                img_y = y + self.thumbnail_size // 2
                img_id = self.thumbnail_canvas.create_image(
                    img_x, img_y, image=thumb_photo, tags=(name, 'img')
                )
                
                # Draw label
                label_y = y + self.thumbnail_size + 5
                label_text = name if len(name) <= 12 else name[:9] + "..."
                label_id = self.thumbnail_canvas.create_text(
                    img_x, label_y, text=label_text, fill='white',
                    font=('Arial', 9), tags=(name, 'label')
                )
                
                # Store item data
                self.thumbnail_items[name] = {
                    'bg': bg_id, 'img': img_id, 'label': label_id,
                    'x': x, 'y': y
                }
                
            except Exception as e:
                print(f"Error creating thumbnail for {name}: {e}")
            
            col += 1
            if col >= cols:
                col = 0
                row += 1
        
        # Update scroll region
        total_rows = (len(filtered_sprites) + cols - 1) // cols
        scroll_height = padding + total_rows * thumb_total_size + 30
        self.thumbnail_canvas.config(scrollregion=(0, 0, canvas_width, scroll_height))
    
    def on_thumbnail_click(self, event):
        """Handle thumbnail click"""
        canvas_x = self.thumbnail_canvas.canvasx(event.x)
        canvas_y = self.thumbnail_canvas.canvasy(event.y)
        
        items = self.thumbnail_canvas.find_overlapping(canvas_x, canvas_y, canvas_x, canvas_y)
        
        if items:
            tags = self.thumbnail_canvas.gettags(items[0])
            name = None
            for tag in tags:
                if tag in self.thumbnail_items:
                    name = tag
                    break
            
            if name:
                # Clear previous selection visuals
                for selected_name in self.selected_thumbnails:
                    if selected_name in self.thumbnail_items:
                        bg_id = self.thumbnail_items[selected_name]['bg']
                        self.thumbnail_canvas.itemconfig(bg_id, outline='#707070', width=2)
                
                self.selected_thumbnails.clear()
                self.selected_thumbnails.add(name)
                
                # Highlight selected
                bg_id = self.thumbnail_items[name]['bg']
                self.thumbnail_canvas.itemconfig(bg_id, outline='#00FF00', width=3)
                
                # Update main view
                self.selected_sprite = name
                self.display_sprite()
    
    def on_thumbnail_ctrl_click(self, event):
        """Handle ctrl+click for multi-selection"""
        canvas_x = self.thumbnail_canvas.canvasx(event.x)
        canvas_y = self.thumbnail_canvas.canvasy(event.y)
        
        items = self.thumbnail_canvas.find_overlapping(canvas_x, canvas_y, canvas_x, canvas_y)
        
        if items:
            tags = self.thumbnail_canvas.gettags(items[0])
            name = None
            for tag in tags:
                if tag in self.thumbnail_items:
                    name = tag
                    break
            
            if name:
                if name in self.selected_thumbnails:
                    # Deselect
                    self.selected_thumbnails.remove(name)
                    bg_id = self.thumbnail_items[name]['bg']
                    self.thumbnail_canvas.itemconfig(bg_id, outline='#707070', width=2)
                else:
                    # Add to selection
                    self.selected_thumbnails.add(name)
                    bg_id = self.thumbnail_items[name]['bg']
                    self.thumbnail_canvas.itemconfig(bg_id, outline='#00FF00', width=3)
                
                # Update display with first selected
                if self.selected_thumbnails:
                    self.selected_sprite = list(self.selected_thumbnails)[0]
                    self.display_sprite()
                    if len(self.selected_thumbnails) > 1:
                        self.info_label.config(text=f"{len(self.selected_thumbnails)} sprites selected")
    
    def on_sprite_select(self, event):
        """Handle sprite selection from list"""
        selection = self.sprite_listbox.curselection()
        if selection:
            # Display first selected sprite
            self.selected_sprite = self.sprite_listbox.get(selection[0])
            self.display_sprite()
            # Update info for multiple selections
            if len(selection) > 1:
                self.info_label.config(text=f"{len(selection)} sprites selected")
    
    def display_sprite(self):
        """Display selected sprite on canvas"""
        if not self.selected_sprite:
            return
        
        sprite = self.sprite_manager.get_sprite(self.selected_sprite)
        if sprite:
            # Update info
            width, height = sprite.get_size()
            self.info_label.config(text=f"{self.selected_sprite} - {width}x{height}px")
            
            # Convert pygame surface to PIL Image
            sprite_string = pg.image.tostring(sprite, 'RGBA')
            pil_image = Image.frombytes('RGBA', sprite.get_size(), sprite_string)
            
            # Apply zoom
            new_width = int(width * self.zoom_level)
            new_height = int(height * self.zoom_level)
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.NEAREST)
            
            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(pil_image)
            
            # Clear canvas and display
            self.preview_canvas.delete("all")
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            x = canvas_width // 2 + self.canvas_offset_x
            y = canvas_height // 2 + self.canvas_offset_y
            self.preview_canvas.create_image(x, y, image=self.photo, anchor=tk.CENTER, tags="sprite")
    
    def zoom_in(self):
        """Zoom in on preview"""
        self.zoom_level = min(self.zoom_level * 1.5, 10.0)
        self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
        self.display_sprite()
    
    def zoom_out(self):
        """Zoom out on preview"""
        self.zoom_level = max(self.zoom_level / 1.5, 0.1)
        self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
        self.display_sprite()
    
    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.zoom_level = 1.0
        self.zoom_label.config(text="100%")
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        self.display_sprite()
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel zoom"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def start_pan(self, event):
        """Start panning the canvas"""
        self.is_panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.preview_canvas.config(cursor="fleur")
    
    def do_pan(self, event):
        """Pan the canvas"""
        if self.is_panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.canvas_offset_x += dx
            self.canvas_offset_y += dy
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.display_sprite()
    
    def end_pan(self, event):
        """End panning the canvas"""
        self.is_panning = False
        self.preview_canvas.config(cursor="")
    
    def load_sprite(self):
        """Load a single sprite from file"""
        file_path = filedialog.askopenfilename(
            title="Load Sprite",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg *.jpeg"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            name = os.path.splitext(os.path.basename(file_path))[0]
            name = self.get_unique_name(name)
            
            try:
                # Verify file exists and is readable
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                if not os.access(file_path, os.R_OK):
                    raise PermissionError(f"Cannot read file: {file_path}")
                
                self.sprite_manager.load_sprite_from_file(name, file_path)
                self.refresh_sprite_list()
                messagebox.showinfo("Success", f"Loaded sprite: {name}\nSize: {self.sprite_manager.get_sprite(name).get_size()}")
            except FileNotFoundError as e:
                messagebox.showerror("Error", f"File not found:\n{str(e)}")
            except PermissionError as e:
                messagebox.showerror("Error", f"Permission denied:\n{str(e)}")
            except pg.error as e:
                messagebox.showerror("Error", f"Pygame error loading image:\n{str(e)}\n\nMake sure the file is a valid image format.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load sprite:\n{str(e)}\n\nFile: {file_path}")
    
    def load_multiple_sprites(self):
        """Load multiple sprites from files"""
        file_paths = filedialog.askopenfilenames(
            title="Load Multiple Sprites",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if file_paths:
            loaded = 0
            for file_path in file_paths:
                name = os.path.splitext(os.path.basename(file_path))[0]
                name = self.get_unique_name(name)
                
                try:
                    self.sprite_manager.load_sprite_from_file(name, file_path)
                    loaded += 1
                except Exception as e:
                    messagebox.showwarning("Warning", f"Failed to load {file_path}: {str(e)}")
            
            self.refresh_sprite_list()
            messagebox.showinfo("Success", f"Loaded {loaded} sprite(s)")
    
    def export_sprite(self):
        """Export selected sprite to file"""
        if not self.selected_sprite:
            messagebox.showwarning("Warning", "No sprite selected")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export Sprite",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialfile=f"{self.selected_sprite}.png"
        )
        
        if file_path:
            sprite = self.sprite_manager.get_sprite(self.selected_sprite)
            try:
                pg.image.save(sprite, file_path)
                messagebox.showinfo("Success", f"Exported sprite to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export sprite: {str(e)}")
    
    def create_sprite(self):
        """Create a new sprite"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Sprite")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        name_var = tk.StringVar(value="new_sprite")
        ttk.Entry(dialog, textvariable=name_var).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Width:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        width_var = tk.IntVar(value=64)
        ttk.Spinbox(dialog, from_=1, to=1024, textvariable=width_var).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Height:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        height_var = tk.IntVar(value=64)
        ttk.Spinbox(dialog, from_=1, to=1024, textvariable=height_var).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Color:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        color_var = tk.StringVar(value="#FFFFFF")
        color_frame = ttk.Frame(dialog)
        color_frame.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ttk.Entry(color_frame, textvariable=color_var, width=10).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(color_frame, text="Pick", command=lambda: self.pick_color(color_var)).pack(side=tk.LEFT, padx=5)
        
        def create():
            name = self.get_unique_name(name_var.get())
            width = width_var.get()
            height = height_var.get()
            color_hex = color_var.get()
            
            try:
                # Convert hex to RGB
                color = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                sprite = pg.Surface((width, height), pg.SRCALPHA)
                sprite.fill(color)
                self.sprite_manager.add_sprite(name, sprite)
                self.refresh_sprite_list()
                dialog.destroy()
                messagebox.showinfo("Success", f"Created sprite: {name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create sprite: {str(e)}")
        
        ttk.Button(dialog, text="Create", command=create).grid(row=4, column=0, columnspan=2, pady=10)
        dialog.columnconfigure(1, weight=1)
    
    def pick_color(self, color_var):
        """Open color picker"""
        color = colorchooser.askcolor(title="Choose Color")
        if color[1]:
            color_var.set(color[1])
    
    def duplicate_sprite(self):
        """Duplicate selected sprite"""
        if not self.selected_sprite:
            messagebox.showwarning("Warning", "No sprite selected")
            return
        
        sprite = self.sprite_manager.get_sprite(self.selected_sprite)
        if sprite:
            new_name = self.get_unique_name(f"{self.selected_sprite}_copy")
            new_sprite = sprite.copy()
            self.sprite_manager.add_sprite(new_name, new_sprite)
            self.refresh_sprite_list()
            messagebox.showinfo("Success", f"Duplicated sprite as: {new_name}")
    
    def rename_sprite(self):
        """Rename selected sprite(s)"""
        # Get selection from appropriate view
        if self.view_mode.get() == "thumbnail":
            if not self.selected_thumbnails:
                messagebox.showwarning("Warning", "No sprite selected")
                return
            sprite_names = list(self.selected_thumbnails)
        else:
            selection = self.sprite_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "No sprite selected")
                return
            sprite_names = [self.sprite_listbox.get(i) for i in selection]
        
        count = len(sprite_names)
        
        if count == 1:
            # Single sprite rename
            old_name = sprite_names[0]
            new_name = simpledialog.askstring("Rename Sprite", "Enter new name:", initialvalue=old_name)
            if new_name and new_name != old_name:
                new_name = self.get_unique_name(new_name)
                sprite = self.sprite_manager.get_sprite(old_name)
                self.sprite_manager.add_sprite(new_name, sprite)
                self.sprite_manager.remove_sprite(old_name)
                self.selected_sprite = new_name
                self.refresh_sprite_list()
                messagebox.showinfo("Success", f"Renamed sprite to: {new_name}")
        else:
            # Multiple sprite rename - batch rename with prefix/suffix
            dialog = tk.Toplevel(self.root)
            dialog.title(f"Batch Rename {count} Sprites")
            dialog.geometry("400x450")
            dialog.transient(self.root)
            dialog.grab_set()
            
            ttk.Label(dialog, text=f"Renaming {count} sprites:", font=('', 10, 'bold')).pack(pady=10)
            
            # Rename options
            options_frame = ttk.LabelFrame(dialog, text="Rename Options", padding=10)
            options_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            rename_mode = tk.StringVar(value="number")
            ttk.Radiobutton(options_frame, text="Add Prefix", variable=rename_mode, value="prefix").pack(anchor=tk.W, pady=2)
            ttk.Radiobutton(options_frame, text="Add Suffix", variable=rename_mode, value="suffix").pack(anchor=tk.W, pady=2)
            ttk.Radiobutton(options_frame, text="Find and Replace", variable=rename_mode, value="replace").pack(anchor=tk.W, pady=2)
            ttk.Radiobutton(options_frame, text="Sequential Numbering", variable=rename_mode, value="number").pack(anchor=tk.W, pady=2)
            
            # Input fields
            input_frame = ttk.Frame(options_frame)
            input_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(input_frame, text="Text/Base Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
            text_var = tk.StringVar(value="")
            text_entry = ttk.Entry(input_frame, textvariable=text_var, width=30)
            text_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)
            
            ttk.Label(input_frame, text="Find (for replace):").grid(row=1, column=0, sticky=tk.W, pady=5)
            find_var = tk.StringVar(value="")
            find_entry = ttk.Entry(input_frame, textvariable=find_var, width=30)
            find_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
            
            ttk.Label(input_frame, text="Start Number:").grid(row=2, column=0, sticky=tk.W, pady=5)
            start_var = tk.IntVar(value=1)
            start_spin = ttk.Spinbox(input_frame, from_=0, to=999, textvariable=start_var, width=28)
            start_spin.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=5)
            
            input_frame.columnconfigure(1, weight=1)
            
            def apply_rename():
                mode = rename_mode.get()
                text = text_var.get()
                find_text = find_var.get()
                start_num = start_var.get()
                
                renamed_count = 0
                for idx, old_name in enumerate(sprite_names):
                    sprite = self.sprite_manager.get_sprite(old_name)
                    new_name = old_name
                    
                    if mode == "prefix":
                        new_name = text + old_name
                    elif mode == "suffix":
                        new_name = old_name + text
                    elif mode == "replace":
                        if find_text in old_name:
                            new_name = old_name.replace(find_text, text)
                    elif mode == "number":
                        base_name = text if text else "sprite"
                        new_name = f"{base_name}_{start_num + idx:03d}"
                    
                    if new_name != old_name:
                        new_name = self.get_unique_name(new_name)
                        self.sprite_manager.add_sprite(new_name, sprite)
                        self.sprite_manager.remove_sprite(old_name)
                        renamed_count += 1
                
                self.selected_sprite = None
                self.refresh_sprite_list()
                dialog.destroy()
                messagebox.showinfo("Success", f"Renamed {renamed_count} sprite(s)")
            
            # Buttons
            button_frame = ttk.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Apply", command=apply_rename).pack(side=tk.RIGHT, padx=5)
    
    def resize_sprite(self):
        """Resize selected sprite"""
        if not self.selected_sprite:
            messagebox.showwarning("Warning", "No sprite selected")
            return
        
        sprite = self.sprite_manager.get_sprite(self.selected_sprite)
        current_width, current_height = sprite.get_size()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Resize Sprite")
        dialog.geometry("250x120")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="New Width:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        width_var = tk.IntVar(value=current_width)
        ttk.Spinbox(dialog, from_=1, to=2048, textvariable=width_var).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="New Height:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        height_var = tk.IntVar(value=current_height)
        ttk.Spinbox(dialog, from_=1, to=2048, textvariable=height_var).grid(row=1, column=1, padx=5, pady=5)
        
        def resize():
            new_width = width_var.get()
            new_height = height_var.get()
            resized_sprite = pg.transform.scale(sprite, (new_width, new_height))
            self.sprite_manager.add_sprite(self.selected_sprite, resized_sprite)
            self.display_sprite()
            dialog.destroy()
            messagebox.showinfo("Success", f"Resized sprite to {new_width}x{new_height}")
        
        ttk.Button(dialog, text="Resize", command=resize).grid(row=2, column=0, columnspan=2, pady=10)
    
    def delete_sprite(self):
        """Delete selected sprite(s)"""
        # Get selection from appropriate view
        if self.view_mode.get() == "thumbnail":
            if not self.selected_thumbnails:
                messagebox.showwarning("Warning", "No sprite selected")
                return
            sprite_names = list(self.selected_thumbnails)
        else:
            selection = self.sprite_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "No sprite selected")
                return
            sprite_names = [self.sprite_listbox.get(i) for i in selection]
        
        count = len(sprite_names)
        
        if count == 1:
            msg = f"Delete sprite '{sprite_names[0]}'?"
        else:
            msg = f"Delete {count} selected sprites?"
        
        if messagebox.askyesno("Confirm Delete", msg):
            for name in sprite_names:
                self.sprite_manager.remove_sprite(name)
            
            self.selected_sprite = None
            self.selected_thumbnails.clear()
            self.preview_canvas.delete("all")
            self.info_label.config(text="No sprite selected")
            self.refresh_sprite_list()
            messagebox.showinfo("Success", f"Deleted {count} sprite(s)")
    
    def clear_all_sprites(self):
        """Clear all sprites"""
        if len(self.sprite_manager.sprites) == 0:
            messagebox.showinfo("Info", "No sprites to clear")
            return
        
        if messagebox.askyesno("Confirm Clear", "Delete all sprites? This cannot be undone."):
            self.sprite_manager.sprites.clear()
            self.selected_sprite = None
            self.preview_canvas.delete("all")
            self.info_label.config(text="No sprite selected")
            self.refresh_sprite_list()
            messagebox.showinfo("Success", "All sprites cleared")
    
    def get_unique_name(self, base_name):
        """Get a unique name by appending numbers if necessary"""
        name = base_name
        counter = 1
        while name in self.sprite_manager.sprites:
            name = f"{base_name}_{counter}"
            counter += 1
        return name
    
    def on_closing(self):
        """Handle window close event"""
        if messagebox.askokcancel("Quit", "Do you want to save before exiting?"):
            self.sprite_manager.save_sprite_data()
            self.sprite_manager.save_sprite_data_as_backup()
            messagebox.showinfo("Saved", "Sprites saved successfully!")
        self.root.destroy()
    
    def save_n_exit(self):
        """Save sprite data and exit"""
        self.sprite_manager.save_sprite_data(self.sprite_manager.default_file_name)
        self.sprite_manager.save_sprite_data(self.sprite_manager.backup_file_name)
        self.root.destroy()
    
    def load_spritesheet(self):
        """Load a spritesheet and split it into individual sprites"""
        file_path = filedialog.askopenfilename(
            title="Load Spritesheet",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        # Load the spritesheet
        try:
            spritesheet = pg.image.load(file_path).convert_alpha()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load spritesheet: {str(e)}")
            return
        
        # Dialog for spritesheet settings
        dialog = tk.Toplevel(self.root)
        dialog.title("Spritesheet Settings")
        dialog.geometry("350x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        sheet_width, sheet_height = spritesheet.get_size()
        
        ttk.Label(dialog, text=f"Spritesheet size: {sheet_width}x{sheet_height}px").grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(dialog, text="Sprite Width:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        sprite_width_var = tk.IntVar(value=32)
        ttk.Spinbox(dialog, from_=1, to=sheet_width, textvariable=sprite_width_var).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Sprite Height:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        sprite_height_var = tk.IntVar(value=32)
        ttk.Spinbox(dialog, from_=1, to=sheet_height, textvariable=sprite_height_var).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Base Name:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        base_name_var = tk.StringVar(value=os.path.splitext(os.path.basename(file_path))[0])
        ttk.Entry(dialog, textvariable=base_name_var).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Horizontal Spacing:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        h_spacing_var = tk.IntVar(value=0)
        ttk.Spinbox(dialog, from_=0, to=100, textvariable=h_spacing_var).grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Vertical Spacing:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        v_spacing_var = tk.IntVar(value=0)
        ttk.Spinbox(dialog, from_=0, to=100, textvariable=v_spacing_var).grid(row=5, column=1, padx=5, pady=5, sticky="ew")
        
        def split_sheet():
            sprite_width = sprite_width_var.get()
            sprite_height = sprite_height_var.get()
            base_name = base_name_var.get()
            h_spacing = h_spacing_var.get()
            v_spacing = v_spacing_var.get()
            
            cols = (sheet_width + h_spacing) // (sprite_width + h_spacing)
            rows = (sheet_height + v_spacing) // (sprite_height + v_spacing)
            
            count = 0
            for row in range(rows):
                for col in range(cols):
                    x = col * (sprite_width + h_spacing)
                    y = row * (sprite_height + v_spacing)
                    
                    # Extract sprite
                    sprite = pg.Surface((sprite_width, sprite_height), pg.SRCALPHA)
                    sprite.blit(spritesheet, (0, 0), (x, y, sprite_width, sprite_height))
                    
                    # Add to manager
                    sprite_name = self.get_unique_name(f"{base_name}_{count}")
                    self.sprite_manager.add_sprite(sprite_name, sprite)
                    count += 1
            
            self.refresh_sprite_list()
            dialog.destroy()
            messagebox.showinfo("Success", f"Split spritesheet into {count} sprites")
        
        ttk.Button(dialog, text="Split", command=split_sheet).grid(row=6, column=0, columnspan=2, pady=15)
        dialog.columnconfigure(1, weight=1)
    
    def export_all_sprites(self):
        """Export all sprites to a folder"""
        folder_path = filedialog.askdirectory(title="Select Export Folder")
        
        if not folder_path:
            return
        
        exported = 0
        for name, sprite in self.sprite_manager.sprites.items():
            try:
                file_path = os.path.join(folder_path, f"{name}.png")
                pg.image.save(sprite, file_path)
                exported += 1
            except Exception as e:
                messagebox.showwarning("Warning", f"Failed to export {name}: {str(e)}")
        
        messagebox.showinfo("Success", f"Exported {exported} sprite(s) to {folder_path}")
    
    def split_sprite(self):
        """Split selected sprite into multiple parts with visual guide"""
        if not self.selected_sprite:
            messagebox.showwarning("Warning", "No sprite selected")
            return
        
        def perform_split():
            mode = split_mode.get()
            piece_count = 0
            
            if mode == "grid":
                cols = cols_var.get()
                rows = rows_var.get()
                piece_width = width // cols
                piece_height = height // rows
                
                for row in range(rows):
                    for col in range(cols):
                        x = col * piece_width
                        y = row * piece_height
                        piece = pg.Surface((piece_width, piece_height), pg.SRCALPHA)
                        piece.blit(sprite, (0, 0), (x, y, piece_width, piece_height))
                        name = self.get_unique_name(f"{self.selected_sprite}_{piece_count}")
                        self.sprite_manager.add_sprite(name, piece)
                        piece_count += 1
            
            elif mode == "fixed":
                pw = piece_width_var.get()
                ph = piece_height_var.get()
                h_space = h_spacing_var.get()
                v_space = v_spacing_var.get()
                
                cols = (width + h_space) // (pw + h_space)
                rows = (height + v_space) // (ph + v_space)
                
                for row in range(rows):
                    for col in range(cols):
                        x = col * (pw + h_space)
                        y = row * (ph + v_space)
                        piece = pg.Surface((pw, ph), pg.SRCALPHA)
                        piece.blit(sprite, (0, 0), (x, y, pw, ph))
                        name = self.get_unique_name(f"{self.selected_sprite}_{piece_count}")
                        self.sprite_manager.add_sprite(name, piece)
                        piece_count += 1
            
            elif mode == "custom":
                for i, rect in enumerate(custom_rects):
                    x1, y1, x2, y2 = rect
                    w = x2 - x1
                    h = y2 - y1
                    piece = pg.Surface((w, h), pg.SRCALPHA)
                    piece.blit(sprite, (0, 0), (x1, y1, w, h))
                    name = self.get_unique_name(f"{self.selected_sprite}_{i}")
                    self.sprite_manager.add_sprite(name, piece)
                    piece_count += 1
            
            if not keep_original_var.get():
                self.sprite_manager.remove_sprite(self.selected_sprite)
            
            self.refresh_sprite_list()
            preview_window.destroy()
            messagebox.showinfo("Success", f"Split into {piece_count} pieces")
        
        sprite = self.sprite_manager.get_sprite(self.selected_sprite)
        width, height = sprite.get_size()
        
        # Create split preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Split Sprite - Visual Guide")
        preview_window.geometry("900x700")
        preview_window.transient(self.root)
        
        # Main layout
        main_frame = ttk.Frame(preview_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Preview canvas
        left_frame = ttk.LabelFrame(main_frame, text="Preview with Guide Lines", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        canvas = tk.Canvas(left_frame, bg='#606060', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Right side - Controls
        right_frame = ttk.LabelFrame(main_frame, text="Split Settings", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(right_frame, text=f"Sprite: {self.selected_sprite}").pack(pady=5)
        ttk.Label(right_frame, text=f"Size: {width}x{height}px").pack(pady=5)
        
        ttk.Separator(right_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Split mode selection
        ttk.Label(right_frame, text="Split Mode:", font=('TkDefaultFont', 10, 'bold')).pack(anchor="w", pady=(5, 2))
        split_mode = tk.StringVar(value="grid")
        ttk.Radiobutton(right_frame, text="Grid (Rows/Columns)", variable=split_mode, value="grid").pack(anchor="w", padx=20)
        ttk.Radiobutton(right_frame, text="Fixed Size", variable=split_mode, value="fixed").pack(anchor="w", padx=20)
        ttk.Radiobutton(right_frame, text="Custom Rectangles", variable=split_mode, value="custom").pack(anchor="w", padx=20)
        
        ttk.Separator(right_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Grid mode controls
        grid_frame = ttk.Frame(right_frame)
        grid_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(grid_frame, text="Columns:").grid(row=0, column=0, sticky="w", pady=2)
        cols_var = tk.IntVar(value=2)
        ttk.Spinbox(grid_frame, from_=1, to=20, textvariable=cols_var, width=10).grid(row=0, column=1, pady=2)
        
        ttk.Label(grid_frame, text="Rows:").grid(row=1, column=0, sticky="w", pady=2)
        rows_var = tk.IntVar(value=2)
        ttk.Spinbox(grid_frame, from_=1, to=20, textvariable=rows_var, width=10).grid(row=1, column=1, pady=2)
        
        # Fixed size mode controls
        fixed_frame = ttk.Frame(right_frame)
        fixed_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(fixed_frame, text="Piece Width:").grid(row=0, column=0, sticky="w", pady=2)
        piece_width_var = tk.IntVar(value=32)
        ttk.Spinbox(fixed_frame, from_=1, to=width, textvariable=piece_width_var, width=10).grid(row=0, column=1, pady=2)
        
        ttk.Label(fixed_frame, text="Piece Height:").grid(row=1, column=0, sticky="w", pady=2)
        piece_height_var = tk.IntVar(value=32)
        ttk.Spinbox(fixed_frame, from_=1, to=height, textvariable=piece_height_var, width=10).grid(row=1, column=1, pady=2)
        
        ttk.Label(fixed_frame, text="H Spacing:").grid(row=2, column=0, sticky="w", pady=2)
        h_spacing_var = tk.IntVar(value=0)
        ttk.Spinbox(fixed_frame, from_=0, to=50, textvariable=h_spacing_var, width=10).grid(row=2, column=1, pady=2)
        
        ttk.Label(fixed_frame, text="V Spacing:").grid(row=3, column=0, sticky="w", pady=2)
        v_spacing_var = tk.IntVar(value=0)
        ttk.Spinbox(fixed_frame, from_=0, to=50, textvariable=v_spacing_var, width=10).grid(row=3, column=1, pady=2)
        
        ttk.Separator(right_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Guide line options
        ttk.Label(right_frame, text="Guide Options:", font=('TkDefaultFont', 10, 'bold')).pack(anchor="w", pady=(5, 2))
        
        show_grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="Show Grid Lines", variable=show_grid_var).pack(anchor="w", padx=20)
        
        show_numbers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="Show Piece Numbers", variable=show_numbers_var).pack(anchor="w", padx=20)
        
        guide_color_var = tk.StringVar(value="#00FF00")
        color_frame = ttk.Frame(right_frame)
        color_frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(color_frame, text="Grid Color:").pack(side=tk.LEFT)
        ttk.Button(color_frame, text="Pick", command=lambda: self.pick_color(guide_color_var), width=8).pack(side=tk.RIGHT)
        
        ttk.Separator(right_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Output options
        ttk.Label(right_frame, text="Output:", font=('TkDefaultFont', 10, 'bold')).pack(anchor="w", pady=(5, 2))
        keep_original_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="Keep Original", variable=keep_original_var).pack(anchor="w", padx=20)
        
        # Preview info label
        info_label = ttk.Label(right_frame, text="Pieces: 0", foreground="blue")
        info_label.pack(pady=10)

        # Split button
        ttk.Button(right_frame, text="Split", command=perform_split).pack(pady=10)

        # Custom rectangles storage
        custom_rects = []
        drag_start = None
        current_rect = None
        canvas_photo_ref = None  # Store PhotoImage reference
        
        
        
        def draw_preview():
            """Draw sprite with guide lines"""
            canvas.delete("all")
            
            # Calculate scaling to fit canvas
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            if canvas_width < 10 or canvas_height < 10:
                canvas.after(100, draw_preview)
                return
            
            scale = min((canvas_width - 40) / width, (canvas_height - 40) / height, 3.0)
            scaled_width = int(width * scale)
            scaled_height = int(height * scale)
            offset_x = (canvas_width - scaled_width) // 2
            offset_y = (canvas_height - scaled_height) // 2
            # Convert sprite to PIL and display
            nonlocal canvas_photo_ref
            sprite_string = pg.image.tostring(sprite, 'RGBA')
            pil_image = Image.frombytes('RGBA', sprite.get_size(), sprite_string)
            pil_image = pil_image.resize((scaled_width, scaled_height), Image.Resampling.NEAREST)
            canvas_photo_ref = ImageTk.PhotoImage(pil_image)
            canvas.create_image(offset_x, offset_y, image=canvas_photo_ref, anchor=tk.NW, tags="sprite")
            
            if not show_grid_var.get():
                return
            
            # Draw guide lines based on mode
            mode = split_mode.get()
            guide_color = guide_color_var.get()
            piece_count = 0
            
            if mode == "grid":
                cols = cols_var.get()
                rows = rows_var.get()
                piece_width = scaled_width / cols
                piece_height = scaled_height / rows
                
                # Draw vertical lines
                for i in range(1, cols):
                    x = offset_x + i * piece_width
                    canvas.create_line(x, offset_y, x, offset_y + scaled_height, fill=guide_color, width=2, tags="guide")
                
                # Draw horizontal lines
                for i in range(1, rows):
                    y = offset_y + i * piece_height
                    canvas.create_line(offset_x, y, offset_x + scaled_width, y, fill=guide_color, width=2, tags="guide")
                
                # Draw piece numbers
                if show_numbers_var.get():
                    for row in range(rows):
                        for col in range(cols):
                            x = offset_x + (col + 0.5) * piece_width
                            y = offset_y + (row + 0.5) * piece_height
                            canvas.create_text(x, y, text=str(piece_count), fill="yellow", 
                                             font=('Arial', 12, 'bold'), tags="guide")
                            piece_count += 1
                
            elif mode == "fixed":
                piece_w = piece_width_var.get()
                piece_h = piece_height_var.get()
                h_space = h_spacing_var.get()
                v_space = v_spacing_var.get()
                
                cols = (width + h_space) // (piece_w + h_space)
                rows = (height + v_space) // (piece_h + v_space)
                
                # Draw grid
                for col in range(cols + 1):
                    x = offset_x + col * (piece_w + h_space) * scale
                    if x <= offset_x + scaled_width:
                        canvas.create_line(x, offset_y, x, offset_y + scaled_height, fill=guide_color, width=2, tags="guide")
                
                for row in range(rows + 1):
                    y = offset_y + row * (piece_h + v_space) * scale
                    if y <= offset_y + scaled_height:
                        canvas.create_line(offset_x, y, offset_x + scaled_width, y, fill=guide_color, width=2, tags="guide")
                
                # Draw piece numbers
                if show_numbers_var.get():
                    for row in range(rows):
                        for col in range(cols):
                            x = offset_x + (col * (piece_w + h_space) + piece_w / 2) * scale
                            y = offset_y + (row * (piece_h + v_space) + piece_h / 2) * scale
                            canvas.create_text(x, y, text=str(piece_count), fill="yellow",
                                             font=('Arial', 12, 'bold'), tags="guide")
                            piece_count += 1
                
            elif mode == "custom":
                # Draw custom rectangles
                for i, rect in enumerate(custom_rects):
                    x1 = offset_x + rect[0] * scale
                    y1 = offset_y + rect[1] * scale
                    x2 = offset_x + rect[2] * scale
                    y2 = offset_y + rect[3] * scale
                    canvas.create_rectangle(x1, y1, x2, y2, outline=guide_color, width=2, tags="guide")
                    if show_numbers_var.get():
                        canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=str(i), 
                                         fill="yellow", font=('Arial', 12, 'bold'), tags="guide")
                piece_count = len(custom_rects)
            
            info_label.config(text=f"Pieces: {piece_count}")
        
        def on_canvas_click(event):
            nonlocal drag_start, current_rect
            if split_mode.get() == "custom":
                drag_start = (event.x, event.y)
        
        def on_canvas_drag(event):
            nonlocal current_rect
            if split_mode.get() == "custom" and drag_start:
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                scale = min((canvas_width - 40) / width, (canvas_height - 40) / height, 3.0)
                scaled_width = int(width * scale)
                scaled_height = int(height * scale)
                offset_x = (canvas_width - scaled_width) // 2
                offset_y = (canvas_height - scaled_height) // 2
                
                if current_rect:
                    canvas.delete(current_rect)
                current_rect = canvas.create_rectangle(drag_start[0], drag_start[1], 
                                                      event.x, event.y, outline="red", width=2, dash=(4, 4))
        
        def on_canvas_release(event):
            nonlocal drag_start, current_rect
            if split_mode.get() == "custom" and drag_start:
                canvas_width = canvas.winfo_width()
                canvas_height = canvas.winfo_height()
                scale = min((canvas_width - 40) / width, (canvas_height - 40) / height, 3.0)
                scaled_width = int(width * scale)
                scaled_height = int(height * scale)
                offset_x = (canvas_width - scaled_width) // 2
                offset_y = (canvas_height - scaled_height) // 2
                
                # Convert canvas coordinates to sprite coordinates
                x1 = max(0, min(width, int((drag_start[0] - offset_x) / scale)))
                y1 = max(0, min(height, int((drag_start[1] - offset_y) / scale)))
                x2 = max(0, min(width, int((event.x - offset_x) / scale)))
                y2 = max(0, min(height, int((event.y - offset_y) / scale)))
                
                if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:  # Minimum size
                    custom_rects.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
                    draw_preview()
                
                if current_rect:
                    canvas.delete(current_rect)
                current_rect = None
                drag_start = None
        
        canvas.bind("<ButtonPress-1>", on_canvas_click)
        canvas.bind("<B1-Motion>", on_canvas_drag)
        canvas.bind("<ButtonRelease-1>", on_canvas_release)
        
        def clear_custom():
            custom_rects.clear()
            draw_preview()
        
        def update_preview(*args):
            draw_preview()
        
        # Bind update events
        cols_var.trace('w', update_preview)
        rows_var.trace('w', update_preview)
        piece_width_var.trace('w', update_preview)
        piece_height_var.trace('w', update_preview)
        h_spacing_var.trace('w', update_preview)
        v_spacing_var.trace('w', update_preview)
        split_mode.trace('w', update_preview)
        show_grid_var.trace('w', update_preview)
        show_numbers_var.trace('w', update_preview)
        guide_color_var.trace('w', update_preview)
        
        # Initial draw
        canvas.after(100, draw_preview)
        
        # Custom mode buttons
        custom_buttons = ttk.Frame(right_frame)
        custom_buttons.pack(fill=tk.X, pady=5)
        ttk.Button(custom_buttons, text="Clear Rects", command=clear_custom).pack(side=tk.LEFT, padx=2)
        
        # Bottom buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(side=tk.BOTTOM, pady=10)
        
        def do_split():
            mode = split_mode.get()
            keep_original = keep_original_var.get()
            count = 0
            
            if mode == "grid":
                cols = cols_var.get()
                rows = rows_var.get()
                piece_width = width // cols
                piece_height = height // rows
                
                for row in range(rows):
                    for col in range(cols):
                        x = col * piece_width
                        y = row * piece_height
                        piece = pg.Surface((piece_width, piece_height), pg.SRCALPHA)
                        piece.blit(sprite, (0, 0), (x, y, piece_width, piece_height))
                        piece_name = self.get_unique_name(f"{self.selected_sprite}_r{row}_c{col}")
                        self.sprite_manager.add_sprite(piece_name, piece)
                        count += 1
                        
            elif mode == "fixed":
                piece_w = piece_width_var.get()
                piece_h = piece_height_var.get()
                h_space = h_spacing_var.get()
                v_space = v_spacing_var.get()
                
                y = 0
                row = 0
                while y + piece_h <= height:
                    x = 0
                    col = 0
                    while x + piece_w <= width:
                        piece = pg.Surface((piece_w, piece_h), pg.SRCALPHA)
                        piece.blit(sprite, (0, 0), (x, y, piece_w, piece_h))
                        piece_name = self.get_unique_name(f"{self.selected_sprite}_{count}")
                        self.sprite_manager.add_sprite(piece_name, piece)
                        count += 1
                        x += piece_w + h_space
                        col += 1
                    y += piece_h + v_space
                    row += 1
                    
            elif mode == "custom":
                for i, rect in enumerate(custom_rects):
                    x1, y1, x2, y2 = rect
                    piece_w = x2 - x1
                    piece_h = y2 - y1
                    piece = pg.Surface((piece_w, piece_h), pg.SRCALPHA)
                    piece.blit(sprite, (0, 0), (x1, y1, piece_w, piece_h))
                    piece_name = self.get_unique_name(f"{self.selected_sprite}_part{i}")
                    self.sprite_manager.add_sprite(piece_name, piece)
                    count += 1
            
            if not keep_original:
                self.sprite_manager.remove_sprite(self.selected_sprite)
                self.selected_sprite = None
                self.preview_canvas.delete("all")
                self.info_label.config(text="No sprite selected")
            
            self.refresh_sprite_list()
            preview_window.destroy()
            messagebox.showinfo("Success", f"Split sprite into {count} pieces")
        
        ttk.Button(button_frame, text="Split", command=do_split).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=preview_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def crop_sprite(self):
        """Crop selected sprite"""
        if not self.selected_sprite:
            messagebox.showwarning("Warning", "No sprite selected")
            return
        
        sprite = self.sprite_manager.get_sprite(self.selected_sprite)
        width, height = sprite.get_size()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Crop Sprite")
        dialog.geometry("300x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Current size: {width}x{height}px").grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(dialog, text="X Position:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        x_var = tk.IntVar(value=0)
        ttk.Spinbox(dialog, from_=0, to=width-1, textvariable=x_var).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Y Position:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        y_var = tk.IntVar(value=0)
        ttk.Spinbox(dialog, from_=0, to=height-1, textvariable=y_var).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Crop Width:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        crop_width_var = tk.IntVar(value=width)
        ttk.Spinbox(dialog, from_=1, to=width, textvariable=crop_width_var).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(dialog, text="Crop Height:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        crop_height_var = tk.IntVar(value=height)
        ttk.Spinbox(dialog, from_=1, to=height, textvariable=crop_height_var).grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        create_new_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Create new sprite (keep original)", variable=create_new_var).grid(row=5, column=0, columnspan=2, pady=5)
        
        def do_crop():
            x = x_var.get()
            y = y_var.get()
            crop_width = crop_width_var.get()
            crop_height = crop_height_var.get()
            create_new = create_new_var.get()
            
            # Validate crop area
            if x + crop_width > width or y + crop_height > height:
                messagebox.showerror("Error", "Crop area exceeds sprite bounds")
                return
            
            # Create cropped surface
            cropped = pg.Surface((crop_width, crop_height), pg.SRCALPHA)
            cropped.blit(sprite, (0, 0), (x, y, crop_width, crop_height))
            
            if create_new:
                new_name = self.get_unique_name(f"{self.selected_sprite}_cropped")
                self.sprite_manager.add_sprite(new_name, cropped)
            else:
                self.sprite_manager.add_sprite(self.selected_sprite, cropped)
            
            self.refresh_sprite_list()
            self.display_sprite()
            dialog.destroy()
            messagebox.showinfo("Success", f"Sprite cropped to {crop_width}x{crop_height}")
        
        ttk.Button(dialog, text="Crop", command=do_crop).grid(row=6, column=0, columnspan=2, pady=10)
        dialog.columnconfigure(1, weight=1)
    
    def rotate_sprite(self):
        """Rotate selected sprite"""
        if not self.selected_sprite:
            messagebox.showwarning("Warning", "No sprite selected")
            return
        
        sprite = self.sprite_manager.get_sprite(self.selected_sprite)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Rotate Sprite")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Rotation angle (degrees):").grid(row=0, column=0, padx=5, pady=10, sticky="w")
        angle_var = tk.IntVar(value=90)
        ttk.Spinbox(dialog, from_=-360, to=360, textvariable=angle_var, increment=90).grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        
        create_new_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(dialog, text="Create new sprite (keep original)", variable=create_new_var).grid(row=1, column=0, columnspan=2, pady=5)
        
        def do_rotate():
            angle = angle_var.get()
            create_new = create_new_var.get()
            
            rotated = pg.transform.rotate(sprite, angle)
            
            if create_new:
                new_name = self.get_unique_name(f"{self.selected_sprite}_rot{angle}")
                self.sprite_manager.add_sprite(new_name, rotated)
            else:
                self.sprite_manager.add_sprite(self.selected_sprite, rotated)
            
            self.refresh_sprite_list()
            self.display_sprite()
            dialog.destroy()
            messagebox.showinfo("Success", f"Sprite rotated {angle} degrees")
        
        ttk.Button(dialog, text="Rotate", command=do_rotate).grid(row=2, column=0, columnspan=2, pady=10)
        dialog.columnconfigure(1, weight=1)
    
    def paint_sprite(self):
        """Paint/draw on selected sprite with brush tools"""
        if not self.selected_sprite:
            messagebox.showwarning("Warning", "No sprite selected")
            return
        
        sprite = self.sprite_manager.get_sprite(self.selected_sprite).copy()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Paint Sprite")
        dialog.geometry("800x650")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Top toolbar
        toolbar = ttk.Frame(dialog)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Brush settings
        ttk.Label(toolbar, text="Brush Size:").pack(side=tk.LEFT, padx=5)
        brush_size_var = tk.IntVar(value=5)
        brush_size_spin = ttk.Spinbox(toolbar, from_=1, to=50, textvariable=brush_size_var, width=5)
        brush_size_spin.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(toolbar, text="Opacity:").pack(side=tk.LEFT, padx=5)
        opacity_var = tk.IntVar(value=255)
        opacity_scale = ttk.Scale(toolbar, from_=0, to=255, variable=opacity_var, orient=tk.HORIZONTAL, length=100)
        opacity_scale.pack(side=tk.LEFT, padx=5)
        
        # Tool selection
        ttk.Label(toolbar, text="Tool:").pack(side=tk.LEFT, padx=5)
        tool_var = tk.StringVar(value="brush")
        ttk.Radiobutton(toolbar, text="Brush", variable=tool_var, value="brush").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(toolbar, text="Eraser", variable=tool_var, value="eraser").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(toolbar, text="Line", variable=tool_var, value="line").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(toolbar, text="Rectangle", variable=tool_var, value="rect").pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(toolbar, text="Circle", variable=tool_var, value="circle").pack(side=tk.LEFT, padx=2)
        
        # Color picker
        current_color = [0, 0, 0, 255]  # RGBA
        color_button = tk.Button(toolbar, text="Color", bg="black", fg="white", width=6)
        color_button.pack(side=tk.LEFT, padx=10)
        
        def pick_color():
            from tkinter import colorchooser
            color = colorchooser.askcolor(title="Choose color")
            if color and color[0]:
                current_color[0] = int(color[0][0])
                current_color[1] = int(color[0][1])
                current_color[2] = int(color[0][2])
                hex_color = color[1] if color[1] else "#000000"
                color_button.config(bg=hex_color, fg="white" if sum(color[0][:3]) < 384 else "black")
        
        color_button.config(command=pick_color)
        
        # Canvas for drawing
        canvas_frame = ttk.Frame(dialog)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(canvas_frame, bg="gray")
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Scale sprite for display (zoom for easier painting)
        zoom_factor = min(700 / sprite.get_width(), 500 / sprite.get_height())
        zoom_factor = max(1, min(zoom_factor, 4))  # Limit zoom between 1x and 4x
        
        display_width = int(sprite.get_width() * zoom_factor)
        display_height = int(sprite.get_height() * zoom_factor)
        
        # Working surface (pygame)
        work_surface = sprite.copy()
        canvas_photo_ref = None  # Store PhotoImage reference to prevent garbage collection
        
        def update_canvas():
            """Update canvas with current sprite state"""
            # Convert pygame surface to PIL Image
            img_str = pg.image.tostring(work_surface, 'RGBA')
            pil_image = Image.frombytes('RGBA', work_surface.get_size(), img_str)
            
            # Scale for display
            pil_image = pil_image.resize((display_width, display_height), Image.Resampling.NEAREST)
            # Convert to PhotoImage and display
            nonlocal canvas_photo_ref
            canvas_photo_ref = ImageTk.PhotoImage(pil_image)
            canvas.delete("all")
            canvas.create_image(display_width // 2, display_height // 2, image=canvas_photo_ref)
            canvas.config(scrollregion=canvas.bbox(tk.ALL))
        
        update_canvas()
        
        # Drawing state
        is_drawing = False
        last_pos = None
        temp_line_start = None
        
        def canvas_to_sprite_coords(x, y):
            """Convert canvas coordinates to sprite pixel coordinates"""
            sprite_x = int(x / zoom_factor)
            sprite_y = int(y / zoom_factor)
            return sprite_x, sprite_y
        
        def draw_brush(x, y):
            """Draw brush stroke at position"""
            sprite_x, sprite_y = canvas_to_sprite_coords(x, y)
            size = brush_size_var.get()
            tool = tool_var.get()
            
            if tool == "eraser":
                color = (0, 0, 0, 0)  # Transparent
            else:
                color = tuple(current_color[:3]) + (opacity_var.get(),)
            
            # Draw circle for brush
            pg.draw.circle(work_surface, color, (sprite_x, sprite_y), max(1, int(size / zoom_factor)))
        
        def on_mouse_down(event):
            nonlocal is_drawing, last_pos, temp_line_start
            is_drawing = True
            last_pos = (event.x, event.y)
            temp_line_start = (event.x, event.y)
            
            tool = tool_var.get()
            if tool in ["brush", "eraser"]:
                draw_brush(event.x, event.y)
                update_canvas()
        
        def on_mouse_drag(event):
            nonlocal last_pos
            if not is_drawing:
                return
            
            tool = tool_var.get()
            if tool in ["brush", "eraser"]:
                # Interpolate between last and current position for smooth lines
                if last_pos:
                    x0, y0 = last_pos
                    x1, y1 = event.x, event.y
                    distance = max(abs(x1 - x0), abs(y1 - y0))
                    steps = max(1, int(distance / 2))
                    
                    for i in range(steps + 1):
                        t = i / max(steps, 1)
                        x = x0 + (x1 - x0) * t
                        y = y0 + (y1 - y0) * t
                        draw_brush(x, y)
                
                update_canvas()
                last_pos = (event.x, event.y)
        
        def on_mouse_up(event):
            nonlocal is_drawing, temp_line_start
            if not is_drawing:
                return
            
            is_drawing = False
            tool = tool_var.get()
            
            if tool in ["line", "rect", "circle"] and temp_line_start:
                sprite_x0, sprite_y0 = canvas_to_sprite_coords(*temp_line_start)
                sprite_x1, sprite_y1 = canvas_to_sprite_coords(event.x, event.y)
                color = tuple(current_color[:3]) + (opacity_var.get(),)
                width = max(1, int(brush_size_var.get() / zoom_factor))
                
                if tool == "line":
                    pg.draw.line(work_surface, color, (sprite_x0, sprite_y0), (sprite_x1, sprite_y1), width)
                elif tool == "rect":
                    rect = pg.Rect(min(sprite_x0, sprite_x1), min(sprite_y0, sprite_y1),
                                   abs(sprite_x1 - sprite_x0), abs(sprite_y1 - sprite_y0))
                    pg.draw.rect(work_surface, color, rect, width)
                elif tool == "circle":
                    center_x = (sprite_x0 + sprite_x1) // 2
                    center_y = (sprite_y0 + sprite_y1) // 2
                    radius = int(((sprite_x1 - sprite_x0) ** 2 + (sprite_y1 - sprite_y0) ** 2) ** 0.5 / 2)
                    if radius > 0:
                        pg.draw.circle(work_surface, color, (center_x, center_y), radius, width)
                
                update_canvas()
            
            temp_line_start = None
        
        canvas.bind("<Button-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_drag)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)
        
        # Bottom buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        def save_changes():
            create_new = messagebox.askyesno("Save Changes", "Create new sprite (keep original)?")
            if create_new:
                new_name = self.get_unique_name(f"{self.selected_sprite}_painted")
                self.sprite_manager.add_sprite(new_name, work_surface)
            else:
                self.sprite_manager.add_sprite(self.selected_sprite, work_surface)
            
            self.refresh_sprite_list()
            self.display_sprite()
            dialog.destroy()
            messagebox.showinfo("Success", "Sprite saved")
        
        def clear_canvas():
            nonlocal work_surface
            work_surface = sprite.copy()
            update_canvas()
        
        ttk.Button(button_frame, text="Clear", command=clear_canvas).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side=tk.RIGHT, padx=5)
    
    def adjust_sprite(self):
        """Adjust brightness and contrast of selected sprite"""
        if not self.selected_sprite:
            messagebox.showwarning("Warning", "No sprite selected")
            return
        
        sprite = self.sprite_manager.get_sprite(self.selected_sprite)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Brightness & Contrast")
        dialog.geometry("600x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Preview canvas
        preview_frame = ttk.LabelFrame(dialog, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        preview_canvas = tk.Canvas(preview_frame, bg="gray")
        preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Adjustment controls
        control_frame = ttk.Frame(dialog)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Brightness
        brightness_frame = ttk.LabelFrame(control_frame, text="Brightness")
        brightness_frame.pack(fill=tk.X, pady=5)
        
        brightness_var = tk.DoubleVar(value=1.0)
        brightness_label = ttk.Label(brightness_frame, text="1.0")
        brightness_label.pack(side=tk.RIGHT, padx=5)
        
        brightness_scale = ttk.Scale(brightness_frame, from_=0.0, to=2.0, variable=brightness_var,
                                      orient=tk.HORIZONTAL)
        brightness_scale.pack(fill=tk.X, padx=5, pady=5)
        
        # Contrast
        contrast_frame = ttk.LabelFrame(control_frame, text="Contrast")
        contrast_frame.pack(fill=tk.X, pady=5)
        
        contrast_var = tk.DoubleVar(value=1.0)
        contrast_label = ttk.Label(contrast_frame, text="1.0")
        contrast_label.pack(side=tk.RIGHT, padx=5)
        
        contrast_scale = ttk.Scale(contrast_frame, from_=0.0, to=3.0, variable=contrast_var,
                                    orient=tk.HORIZONTAL)
        contrast_scale.pack(fill=tk.X, padx=5, pady=5)
        # Current adjusted surface
        adjusted_surface = sprite.copy()
        preview_photo_ref = None  # Store PhotoImage reference to prevent garbage collection
        
        def update_preview():
            """Update preview with current adjustments"""
            brightness = brightness_var.get()
            contrast = contrast_var.get()
            
            brightness_label.config(text=f"{brightness:.2f}")
            contrast_label.config(text=f"{contrast:.2f}")
            
            # Convert pygame surface to PIL Image
            img_str = pg.image.tostring(sprite, 'RGBA')
            pil_image = Image.frombytes('RGBA', sprite.get_size(), img_str)
            
            # Apply adjustments using PIL ImageEnhance
            from PIL import ImageEnhance
            
            # Brightness
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(pil_image)
                pil_image = enhancer.enhance(brightness)
            
            # Contrast
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(pil_image)
                pil_image = enhancer.enhance(contrast)
            
            # Scale for preview
            max_width = 550
            max_height = 400
            img_width, img_height = pil_image.size
            scale = min(max_width / img_width, max_height / img_height, 1)
            
            if scale < 1:
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert back to pygame surface for storage
            img_bytes = pil_image.tobytes()
            nonlocal adjusted_surface
            # Display in canvas
            nonlocal preview_photo_ref
            preview_photo_ref = ImageTk.PhotoImage(pil_image)
            preview_canvas.delete("all")
            preview_canvas.create_image(pil_image.width // 2, pil_image.height // 2, image=preview_photo_ref)  # Keep reference

        # Bind slider changes
        def on_brightness_change(event=None):
            update_preview()
        
        def on_contrast_change(event=None):
            update_preview()
        
        brightness_scale.config(command=on_brightness_change)
        contrast_scale.config(command=on_contrast_change)
        
        # Initial preview
        update_preview()
        
        # Reset button
        def reset_adjustments():
            brightness_var.set(1.0)
            contrast_var.set(1.0)
            update_preview()
        
        # Bottom buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def apply_adjustments():
            create_new = messagebox.askyesno("Apply Adjustments", "Create new sprite (keep original)?")
            
            # Get final adjusted surface
            brightness = brightness_var.get()
            contrast = contrast_var.get()
            
            # Convert and apply adjustments
            img_str = pg.image.tostring(sprite, 'RGBA')
            pil_image = Image.frombytes('RGBA', sprite.get_size(), img_str)
            
            from PIL import ImageEnhance
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(pil_image)
                pil_image = enhancer.enhance(brightness)
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(pil_image)
                pil_image = enhancer.enhance(contrast)
            
            # Convert back to pygame surface
            img_bytes = pil_image.tobytes()
            final_surface = pg.image.fromstring(img_bytes, pil_image.size, 'RGBA')
            
            if create_new:
                new_name = self.get_unique_name(f"{self.selected_sprite}_adjusted")
                self.sprite_manager.add_sprite(new_name, final_surface)
            else:
                self.sprite_manager.add_sprite(self.selected_sprite, final_surface)
            
            self.refresh_sprite_list()
            self.display_sprite()
            dialog.destroy()
            messagebox.showinfo("Success", "Adjustments applied")
        
        ttk.Button(button_frame, text="Reset", command=reset_adjustments).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Apply", command=apply_adjustments).pack(side=tk.RIGHT, padx=5)
    
    def split_by_transparency(self):
        """Split sprite by detecting non-transparent regions"""
        if not self.selected_sprite:
            messagebox.showwarning("Warning", "No sprite selected")
            return
        
        sprite = self.sprite_manager.get_sprite(self.selected_sprite)
        width, height = sprite.get_size()
        
        # Dialog for settings
        dialog = tk.Toplevel(self.root)
        dialog.title("Split by Transparency")
        dialog.geometry("450x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Detecting non-transparent regions in: {self.selected_sprite}").pack(pady=10)
        ttk.Label(dialog, text=f"Sprite size: {width}x{height}px").pack(pady=5)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(dialog, text="Detection Settings", padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(settings_frame, text="Alpha Threshold:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        alpha_threshold_var = tk.IntVar(value=10)
        ttk.Spinbox(settings_frame, from_=0, to=255, textvariable=alpha_threshold_var, width=10).grid(row=0, column=1, sticky="w", pady=5, padx=5)
        ttk.Label(settings_frame, text="(pixels with alpha > this are considered solid)").grid(row=0, column=2, sticky="w", pady=5, padx=5)
        
        ttk.Label(settings_frame, text="Min Width:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        min_width_var = tk.IntVar(value=4)
        ttk.Spinbox(settings_frame, from_=1, to=width, textvariable=min_width_var, width=10).grid(row=1, column=1, sticky="w", pady=5, padx=5)
        ttk.Label(settings_frame, text="(minimum sprite width)").grid(row=1, column=2, sticky="w", pady=5, padx=5)
        
        ttk.Label(settings_frame, text="Min Height:").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        min_height_var = tk.IntVar(value=4)
        ttk.Spinbox(settings_frame, from_=1, to=height, textvariable=min_height_var, width=10).grid(row=2, column=1, sticky="w", pady=5, padx=5)
        ttk.Label(settings_frame, text="(minimum sprite height)").grid(row=2, column=2, sticky="w", pady=5, padx=5)
        
        ttk.Label(settings_frame, text="Padding:").grid(row=3, column=0, sticky="w", pady=5, padx=5)
        padding_var = tk.IntVar(value=0)
        ttk.Spinbox(settings_frame, from_=0, to=50, textvariable=padding_var, width=10).grid(row=3, column=1, sticky="w", pady=5, padx=5)
        ttk.Label(settings_frame, text="(extra pixels around each sprite)").grid(row=3, column=2, sticky="w", pady=5, padx=5)
        
        # Output options
        output_frame = ttk.LabelFrame(dialog, text="Output Options", padding=10)
        output_frame.pack(fill=tk.X, padx=10, pady=10)
        
        keep_original_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(output_frame, text="Keep Original Sprite", variable=keep_original_var).pack(anchor="w")
        
        sort_mode_var = tk.StringVar(value="left_to_right")
        ttk.Label(output_frame, text="Sort sprites by:").pack(anchor="w", pady=(10, 2))
        ttk.Radiobutton(output_frame, text="Left to Right", variable=sort_mode_var, value="left_to_right").pack(anchor="w", padx=20)
        ttk.Radiobutton(output_frame, text="Top to Bottom", variable=sort_mode_var, value="top_to_bottom").pack(anchor="w", padx=20)
        ttk.Radiobutton(output_frame, text="Size (largest first)", variable=sort_mode_var, value="size").pack(anchor="w", padx=20)
        
        # Info label
        info_label = ttk.Label(dialog, text="", foreground="blue")
        info_label.pack(pady=5)
        
        def detect_and_split():
            """Detect non-transparent regions and split them into separate sprites"""
            alpha_threshold = alpha_threshold_var.get()
            min_width = min_width_var.get()
            min_height = min_height_var.get()
            padding = padding_var.get()
            sort_mode = sort_mode_var.get()
            
            # Create a mask of non-transparent pixels
            pixel_array = pg.surfarray.array3d(sprite)
            alpha_array = pg.surfarray.array_alpha(sprite)
            
            # Create visited map
            visited = [[False for _ in range(height)] for _ in range(width)]
            
            def flood_fill(start_x, start_y):
                """Flood fill to find connected non-transparent region, returns bounding box"""
                if start_x < 0 or start_x >= width or start_y < 0 or start_y >= height:
                    return None
                if visited[start_x][start_y]:
                    return None
                if alpha_array[start_x][start_y] <= alpha_threshold:
                    return None
                
                # BFS to find all connected pixels
                queue = [(start_x, start_y)]
                visited[start_x][start_y] = True
                min_x, max_x = start_x, start_x
                min_y, max_y = start_y, start_y
                
                while queue:
                    x, y = queue.pop(0)
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
                    
                    # Check 4-connected neighbors
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            if not visited[nx][ny] and alpha_array[nx][ny] > alpha_threshold:
                                visited[nx][ny] = True
                                queue.append((nx, ny))
                
                return (min_x, min_y, max_x, max_y)
            
            # Find all regions
            regions = []
            for x in range(width):
                for y in range(height):
                    if not visited[x][y] and alpha_array[x][y] > alpha_threshold:
                        bbox = flood_fill(x, y)
                        if bbox:
                            min_x, min_y, max_x, max_y = bbox
                            w = max_x - min_x + 1
                            h = max_y - min_y + 1
                            
                            # Filter by minimum size
                            if w >= min_width and h >= min_height:
                                # Apply padding
                                min_x = max(0, min_x - padding)
                                min_y = max(0, min_y - padding)
                                max_x = min(width - 1, max_x + padding)
                                max_y = min(height - 1, max_y + padding)
                                
                                regions.append((min_x, min_y, max_x, max_y))
            
            if not regions:
                messagebox.showwarning("No Sprites Found", "No non-transparent regions detected with current settings.")
                return
            
            # Sort regions based on user preference
            if sort_mode == "left_to_right":
                regions.sort(key=lambda r: (r[0], r[1]))  # Sort by x, then y
            elif sort_mode == "top_to_bottom":
                regions.sort(key=lambda r: (r[1], r[0]))  # Sort by y, then x
            elif sort_mode == "size":
                regions.sort(key=lambda r: (r[2] - r[0]) * (r[3] - r[1]), reverse=True)  # Sort by area
            
            # Extract sprites
            count = 0
            for i, (min_x, min_y, max_x, max_y) in enumerate(regions):
                w = max_x - min_x + 1
                h = max_y - min_y + 1
                
                # Create new surface for this region
                region_sprite = pg.Surface((w, h), pg.SRCALPHA)
                region_sprite.blit(sprite, (0, 0), (min_x, min_y, w, h))
                
                # Add to manager
                sprite_name = self.get_unique_name(f"{self.selected_sprite}_split{i}")
                self.sprite_manager.add_sprite(sprite_name, region_sprite)
                count += 1
            
            # Remove original if requested
            if not keep_original_var.get():
                self.sprite_manager.remove_sprite(self.selected_sprite)
                self.selected_sprite = None
                self.preview_canvas.delete("all")
                self.info_label.config(text="No sprite selected")
            
            self.refresh_sprite_list()
            dialog.destroy()
            messagebox.showinfo("Success", f"Split sprite into {count} separate sprites by transparency")
        
        # Preview button
        def preview_detection():
            """Show preview of detected regions"""
            alpha_threshold = alpha_threshold_var.get()
            min_width = min_width_var.get()
            min_height = min_height_var.get()
            padding = padding_var.get()
            
            # Quick detection for count
            pixel_array = pg.surfarray.array3d(sprite)
            alpha_array = pg.surfarray.array_alpha(sprite)
            visited = [[False for _ in range(height)] for _ in range(width)]
            
            def quick_flood(start_x, start_y):
                if start_x < 0 or start_x >= width or start_y < 0 or start_y >= height:
                    return None
                if visited[start_x][start_y]:
                    return None
                if alpha_array[start_x][start_y] <= alpha_threshold:
                    return None
                
                queue = [(start_x, start_y)]
                visited[start_x][start_y] = True
                min_x, max_x = start_x, start_x
                min_y, max_y = start_y, start_y
                
                while queue:
                    x, y = queue.pop(0)
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
                    
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            if not visited[nx][ny] and alpha_array[nx][ny] > alpha_threshold:
                                visited[nx][ny] = True
                                queue.append((nx, ny))
                
                return (min_x, min_y, max_x, max_y)
            
            regions = []
            for x in range(width):
                for y in range(height):
                    if not visited[x][y] and alpha_array[x][y] > alpha_threshold:
                        bbox = quick_flood(x, y)
                        if bbox:
                            min_x, min_y, max_x, max_y = bbox
                            w = max_x - min_x + 1
                            h = max_y - min_y + 1
                            if w >= min_width and h >= min_height:
                                regions.append((min_x, min_y, max_x, max_y))
            
            info_label.config(text=f"Will detect {len(regions)} sprite(s)")
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Preview Count", command=preview_detection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Split", command=detect_and_split).pack(side=tk.RIGHT, padx=5)
    
if __name__ == "__main__":
    # For testing purposes, create a SpriteManager and run the GUI
    from sprite_manager import SpriteManager
    sprite_manager = SpriteManager()
    sprite_manager.RunSpriteManagerGUI()