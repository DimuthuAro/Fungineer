    def setup_sprite_list_panel(self, parent):
        """Setup left panel with sprite list"""
        list_frame = ttk.LabelFrame(parent, text="Sprites", padding="5")
        list_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 5))
        
        # Search bar
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_sprite_list())
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Sprite listbox with scrollbar
        list_scroll_frame = ttk.Frame(list_frame)
        list_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.sprite_listbox = tk.Listbox(list_scroll_frame, yscrollcommand=scrollbar.set, width=30, selectmode=tk.EXTENDED)
        self.sprite_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sprite_listbox.bind('<<ListboxSelect>>', self.on_sprite_select)
        
        scrollbar.config(command=self.sprite_listbox.yview)
        
        # Sprite count label
        self.count_label = ttk.Label(list_frame, text="Total sprites: 0")
        self.count_label.pack(pady=(5, 0))