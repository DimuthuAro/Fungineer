 def setup_preview_panel(self, parent):
        """Setup right panel with sprite preview"""
        preview_frame = ttk.LabelFrame(parent, text="Preview", padding="5")
        preview_frame.grid(row=0, column=1, sticky="nsew")
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
        self.preview_canvas.bind("<ButtonPress-2>", self.start_pan)  # Middle mouse button
        self.preview_canvas.bind("<B2-Motion>", self.do_pan)
        self.preview_canvas.bind("<ButtonRelease-2>", self.end_pan)
        # Also support right-click drag for panning
        self.preview_canvas.bind("<ButtonPress-3>", self.start_pan)
        self.preview_canvas.bind("<B3-Motion>", self.do_pan)
        self.preview_canvas.bind("<ButtonRelease-3>", self.end_pan)