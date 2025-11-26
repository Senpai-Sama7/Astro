"""
ASTRO - Autonomous Agent Ecosystem
Beautiful Modern GUI with Premium Dark Theme
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import asyncio
import queue
import logging
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.engine import AgentEngine
from core.nl_interface import NaturalLanguageInterface
from core.llm_factory import LLMFactory
from monitoring.monitoring_dashboard import MonitoringDashboard
from main import AutonomousAgentEcosystem

# Configure CustomTkinter with premium dark theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Color Palette
COLORS = {
    "bg_dark": "#0d1117",
    "bg_card": "#161b22",
    "bg_input": "#21262d",
    "border": "#30363d",
    "accent": "#58a6ff",
    "accent_hover": "#388bfd",
    "success": "#3fb950",
    "warning": "#d29922",
    "error": "#f85149",
    "text": "#c9d1d9",
    "text_muted": "#8b949e",
    "text_bright": "#f0f6fc",
}


class AgentCard(ctk.CTkFrame):
    """Beautiful agent status card with glassmorphism effect"""
    
    def __init__(self, master, agent_id, capabilities, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )
        
        # Friendly agent names
        friendly_names = {
            "research_agent_001": "🔬 Research Agent",
            "code_agent_001": "💻 Code Agent", 
            "filesystem_agent_001": "📁 File Agent"
        }
        display_name = friendly_names.get(agent_id, agent_id)
        
        # Header with icon and name
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(12, 8))
        
        self.name_label = ctk.CTkLabel(
            header, 
            text=display_name,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_bright"]
        )
        self.name_label.pack(side="left")
        
        # Status indicator (right side)
        self.status_indicator = ctk.CTkLabel(
            header, 
            text="●",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"]
        )
        self.status_indicator.pack(side="right")
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(
            self, 
            height=4, 
            corner_radius=2,
            fg_color=COLORS["bg_input"],
            progress_color=COLORS["accent"]
        )
        self.progress.pack(fill="x", padx=12, pady=(0, 8))
        self.progress.set(0)
        
        # Status text
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        )
        self.status_label.pack(padx=12, pady=(0, 12), anchor="w")
        
    def set_status(self, status, progress=0):
        status_config = {
            "idle": (COLORS["text_muted"], "Ready"),
            "active": (COLORS["success"], "Active"),
            "busy": (COLORS["warning"], "Working..."),
            "failed": (COLORS["error"], "Error")
        }
        color, text = status_config.get(status.lower(), (COLORS["text_muted"], status))
        self.status_indicator.configure(text_color=color)
        self.status_label.configure(text=text, text_color=color)
        self.progress.set(min(progress, 1.0))


class WorkflowItem(ctk.CTkFrame):
    """Workflow history item with status badge"""
    
    def __init__(self, master, workflow_name, status, time_str, workflow_id=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            fg_color=COLORS["bg_input"],
            corner_radius=8,
            height=50
        )
        self.workflow_id = workflow_id
        self.pack_propagate(False)
        
        # Content container
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=8)
        
        # Left: Time and name
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            left, 
            text=time_str,
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            left,
            text=workflow_name[:35] + "..." if len(workflow_name) > 35 else workflow_name,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"]
        ).pack(anchor="w")
        
        # Right: Status badge
        self.status_colors = {
            "running": COLORS["warning"],
            "completed": COLORS["success"],
            "failed": COLORS["error"],
            "pending": COLORS["text_muted"]
        }
        
        self.badge = ctk.CTkLabel(
            content,
            text=status.upper(),
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=self.status_colors.get(status, COLORS["text_muted"]),
            fg_color=COLORS["bg_card"],
            corner_radius=4,
            padx=8,
            pady=2
        )
        self.badge.pack(side="right", pady=5)

    def update_status(self, status):
        self.badge.configure(
            text=status.upper(),
            text_color=self.status_colors.get(status, COLORS["text_muted"])
        )

class EnhancedGUI(ctk.CTk):
    """Main application window with premium dark theme"""
    
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("✨ ASTRO - Your AI Team")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Initialize state
        self.ecosystem = AutonomousAgentEcosystem()
        self.log_queue = queue.Queue()
        self.agent_cards = {}
        self.workflow_items = []
        self.running = False
        self.loop = None
        
        # Setup logging
        self.setup_logging()
        
        # Main layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create UI components
        self.create_sidebar()
        self.create_main_content()
        
        # Start processing loops
        self.after(100, self.process_logs)
        self.after(1000, self.update_status)

    def create_sidebar(self):
        """Premium sidebar with glassmorphism effect"""
        self.sidebar = ctk.CTkFrame(
            self, 
            width=300, 
            corner_radius=0, 
            fg_color=COLORS["bg_card"],
            border_width=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(8, weight=1)
        
        # Logo Section
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=24, pady=(28, 0), sticky="ew")
        
        ctk.CTkLabel(
            logo_frame, 
            text="✨ ASTRO",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COLORS["text_bright"]
        ).pack(side="left")
        
        # Tagline
        ctk.CTkLabel(
            self.sidebar,
            text="Your Personal AI Team",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"]
        ).grid(row=1, column=0, padx=24, pady=(4, 20), sticky="w")
        
        # System Status Card
        self.status_card = ctk.CTkFrame(
            self.sidebar, 
            fg_color=COLORS["bg_input"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"]
        )
        self.status_card.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        status_content = ctk.CTkFrame(self.status_card, fg_color="transparent")
        status_content.pack(fill="x", padx=16, pady=14)
        
        self.system_status_dot = ctk.CTkLabel(
            status_content, 
            text="●",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_muted"]
        )
        self.system_status_dot.pack(side="left")
        
        self.system_status_text = ctk.CTkLabel(
            status_content, 
            text="System Offline",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"]
        )
        self.system_status_text.pack(side="left", padx=(8, 0))
        
        # Control Buttons Section
        ctk.CTkLabel(
            self.sidebar,
            text="CONTROLS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_muted"]
        ).grid(row=3, column=0, padx=24, pady=(0, 8), sticky="w")
        
        # Button container
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.grid(row=4, column=0, padx=20, sticky="ew")
        
        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="▶  Start System",
            command=self.start_system,
            fg_color=COLORS["success"],
            hover_color="#2ea043",
            height=42,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.start_btn.pack(fill="x", pady=(0, 8))
        
        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹  Stop System",
            command=self.stop_system,
            fg_color=COLORS["error"],
            hover_color="#da3633",
            height=42,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.stop_btn.pack(fill="x", pady=(0, 8))
        
        # Secondary buttons in row
        secondary_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
        secondary_frame.pack(fill="x")
        
        ctk.CTkButton(
            secondary_frame,
            text="⚙️ Settings",
            command=self.open_settings,
            fg_color=COLORS["bg_input"],
            hover_color=COLORS["border"],
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"]
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        ctk.CTkButton(
            secondary_frame,
            text="🗑️ Clear",
            command=self.clear_logs,
            fg_color=COLORS["bg_input"],
            hover_color=COLORS["border"],
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"]
        ).pack(side="right", fill="x", expand=True, padx=(4, 0))
        
        # Agents Section
        ctk.CTkLabel(
            self.sidebar,
            text="AI AGENTS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_muted"]
        ).grid(row=7, column=0, padx=24, pady=(24, 8), sticky="w")
        
        # Scrollable agent cards
        self.agents_frame = ctk.CTkScrollableFrame(
            self.sidebar, 
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["text_muted"]
        )
        self.agents_frame.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="nsew")

    def open_settings(self):
        """Open settings dialog"""
        if not hasattr(self, 'settings_window') or not self.settings_window.winfo_exists():
            self.settings_window = SettingsDialog(self)
        else:
            self.settings_window.focus()


class SettingsDialog(ctk.CTkToplevel):
    """Premium settings dialog"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Settings")
        self.geometry("450x550")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Center on parent
        self.transient(parent)
        
        # Wait for window to be created before setting grab
        self.after(150, self._setup_grab)
        
        # Build UI
        self._build_ui()
        
        # Focus this window
        self.focus_force()
        self.lift()
        
    def _setup_grab(self):
        """Setup modal grab after window is visible"""
        try:
            if self.winfo_exists() and self.winfo_viewable():
                self.grab_set()
        except Exception:
            pass
    
    def _build_ui(self):
        """Build the settings UI"""
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="⚙️ Configuration",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_bright"]
        ).pack(expand=True)
        
        # Content frame
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=20)
        
        # Provider Selection
        ctk.CTkLabel(
            content,
            text="AI Provider",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w", pady=(0, 6))
        
        self.provider_var = ctk.StringVar(value=os.getenv("LLM_PROVIDER", "openai"))
        provider_menu = ctk.CTkOptionMenu(
            content,
            variable=self.provider_var,
            values=["openai", "openrouter", "ollama"],
            fg_color=COLORS["bg_input"],
            button_color=COLORS["border"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_input"],
            dropdown_text_color=COLORS["text"],
            text_color=COLORS["text"],
            height=40,
            corner_radius=8
        )
        provider_menu.pack(fill="x", pady=(0, 16))
        
        # Model Name
        ctk.CTkLabel(
            content,
            text="Model Name",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w", pady=(0, 6))
        
        self.model_entry = ctk.CTkEntry(
            content,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["text_muted"],
            height=40,
            corner_radius=8
        )
        self.model_entry.insert(0, os.getenv("LLM_MODEL", "gpt-3.5-turbo"))
        self.model_entry.pack(fill="x", pady=(0, 16))
        
        # API Key
        ctk.CTkLabel(
            content,
            text="API Key",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w", pady=(0, 6))
        
        self.api_key_entry = ctk.CTkEntry(
            content,
            show="•",
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["text_muted"],
            height=40,
            corner_radius=8,
            placeholder_text="sk-... or your API key"
        )
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            self.api_key_entry.insert(0, api_key)
        self.api_key_entry.pack(fill="x", pady=(0, 16))
        
        # Base URL
        ctk.CTkLabel(
            content,
            text="Base URL (Optional - for Ollama)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w", pady=(0, 6))
        
        self.base_url_entry = ctk.CTkEntry(
            content,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["text_muted"],
            height=40,
            corner_radius=8,
            placeholder_text="http://localhost:11434/v1"
        )
        base_url = os.getenv("LLM_BASE_URL", "")
        if base_url:
            self.base_url_entry.insert(0, base_url)
        self.base_url_entry.pack(fill="x", pady=(0, 24))
        
        # Save Button
        ctk.CTkButton(
            content,
            text="💾 Save Configuration",
            command=self.save_settings,
            fg_color=COLORS["success"],
            hover_color="#2ea043",
            text_color=COLORS["text_bright"],
            height=46,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(fill="x")
        
        # Cancel Button
        ctk.CTkButton(
            content,
            text="Cancel",
            command=self.destroy,
            fg_color="transparent",
            hover_color=COLORS["bg_input"],
            text_color=COLORS["text_muted"],
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12)
        ).pack(fill="x", pady=(8, 0))
                     
    def save_settings(self):
        """Save settings and update parent"""
        os.environ["LLM_PROVIDER"] = self.provider_var.get()
        os.environ["LLM_MODEL"] = self.model_entry.get()
        
        api_key = self.api_key_entry.get()
        if api_key and not api_key.startswith("sk-..."):
            os.environ["OPENAI_API_KEY"] = api_key
            
        base_url = self.base_url_entry.get()
        if base_url and base_url != "http://localhost:11434/v1":
            os.environ["LLM_BASE_URL"] = base_url
        
        # Force re-initialization of LLM client
        if hasattr(self.parent, 'llm_client'):
            delattr(self.parent, 'llm_client')
        if hasattr(self.parent, 'nl_interface'):
            delattr(self.parent, 'nl_interface')
            
        logging.info("✅ Settings saved successfully")
        self.destroy()


# Add remaining methods to EnhancedGUI class
EnhancedGUI.create_main_content = lambda self: _create_main_content_impl(self)
EnhancedGUI.create_enhanced_chat = lambda self: _create_enhanced_chat_impl(self)
EnhancedGUI.create_enhanced_logs = lambda self: _create_enhanced_logs_impl(self)
EnhancedGUI.create_workflow_history = lambda self: _create_workflow_history_impl(self)
EnhancedGUI.setup_logging = lambda self: _setup_logging_impl(self)
EnhancedGUI.process_logs = lambda self: _process_logs_impl(self)
EnhancedGUI.update_status = lambda self: _update_status_impl(self)
EnhancedGUI.start_system = lambda self: _start_system_impl(self)
EnhancedGUI.stop_system = lambda self: _stop_system_impl(self)
EnhancedGUI.clear_logs = lambda self: _clear_logs_impl(self)
EnhancedGUI.run_async_loop = lambda self: _run_async_loop_impl(self)
EnhancedGUI.handle_input_btn = lambda self: _handle_input_btn_impl(self)
EnhancedGUI.handle_input = lambda self, event: _handle_input_impl(self, event)
EnhancedGUI.process_command = lambda self, cmd: _process_command_impl(self, cmd)
EnhancedGUI._process_command_async = lambda self, cmd: _process_command_async_impl(self, cmd)


def _create_main_content_impl(self):
    """Premium main content area"""
    self.main_area = ctk.CTkFrame(self, fg_color="transparent")
    self.main_area.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
    self.main_area.grid_columnconfigure(0, weight=2)
    self.main_area.grid_columnconfigure(1, weight=1)
    self.main_area.grid_rowconfigure(1, weight=1)

    # Create sub-components
    self.create_enhanced_chat()
    self.create_enhanced_logs()
    self.create_workflow_history()


def _create_enhanced_chat_impl(self):
    """Premium command input area"""
    chat_container = ctk.CTkFrame(
        self.main_area, 
        fg_color=COLORS["bg_card"],
        corner_radius=16,
        border_width=1,
        border_color=COLORS["border"]
    )
    chat_container.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
    chat_container.grid_columnconfigure(0, weight=1)
    
    # Header
    header_frame = ctk.CTkFrame(chat_container, fg_color="transparent")
    header_frame.grid(row=0, column=0, padx=24, pady=(20, 8), sticky="ew")
    
    ctk.CTkLabel(
        header_frame, 
        text="💬 Command Center",
        font=ctk.CTkFont(size=18, weight="bold"),
        text_color=COLORS["text_bright"]
    ).pack(side="left")
    
    # Help text
    ctk.CTkLabel(
        chat_container,
        text="Tell your AI team what to do using natural language",
        font=ctk.CTkFont(size=12),
        text_color=COLORS["text_muted"]
    ).grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")
    
    # Input area
    input_frame = ctk.CTkFrame(chat_container, fg_color="transparent")
    input_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
    input_frame.grid_columnconfigure(0, weight=1)
    
    self.input_entry = ctk.CTkEntry(
        input_frame,
        placeholder_text="Try: 'Research AI trends and create a summary report'",
        height=52,
        border_width=1,
        border_color=COLORS["border"],
        fg_color=COLORS["bg_input"],
        font=ctk.CTkFont(size=14),
        text_color=COLORS["text"]
    )
    self.input_entry.grid(row=0, column=0, padx=(0, 12), sticky="ew")
    self.input_entry.bind("<Return>", self.handle_input)
    
    self.send_btn = ctk.CTkButton(
        input_frame,
        text="Execute ▶",
        width=130,
        height=52,
        command=self.handle_input_btn,
        corner_radius=10,
        fg_color=COLORS["accent"],
        hover_color=COLORS["accent_hover"],
        font=ctk.CTkFont(size=14, weight="bold")
    )
    self.send_btn.grid(row=0, column=1)


def _create_enhanced_logs_impl(self):
    """Premium activity log panel"""
    log_container = ctk.CTkFrame(
        self.main_area,
        fg_color=COLORS["bg_card"],
        corner_radius=16,
        border_width=1,
        border_color=COLORS["border"]
    )
    log_container.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
    
    # Header
    header_frame = ctk.CTkFrame(log_container, fg_color="transparent")
    header_frame.pack(fill="x", padx=20, pady=(16, 12))
    
    ctk.CTkLabel(
        header_frame,
        text="📡 Activity Log",
        font=ctk.CTkFont(size=15, weight="bold"),
        text_color=COLORS["text_bright"]
    ).pack(side="left")
    
    # Auto-scroll toggle
    self.autoscroll_var = tk.BooleanVar(value=True)
    ctk.CTkCheckBox(
        header_frame,
        text="Auto-scroll",
        variable=self.autoscroll_var,
        font=ctk.CTkFont(size=11),
        text_color=COLORS["text_muted"],
        fg_color=COLORS["accent"],
        hover_color=COLORS["accent_hover"],
        border_color=COLORS["border"]
    ).pack(side="right")
    
    # Log text
    self.log_text = ctk.CTkTextbox(
        log_container,
        fg_color=COLORS["bg_input"],
        text_color=COLORS["text"],
        font=("JetBrains Mono", 11),
        wrap="word",
        corner_radius=8
    )
    self.log_text.pack(fill="both", expand=True, padx=16, pady=(0, 16))


def _create_workflow_history_impl(self):
    """Premium workflow history panel"""
    history_container = ctk.CTkFrame(
        self.main_area,
        fg_color=COLORS["bg_card"],
        corner_radius=16,
        border_width=1,
        border_color=COLORS["border"]
    )
    history_container.grid(row=1, column=1, sticky="nsew")
    
    # Header
    ctk.CTkLabel(
        history_container,
        text="📜 Workflow History",
        font=ctk.CTkFont(size=15, weight="bold"),
        text_color=COLORS["text_bright"]
    ).pack(padx=20, pady=(16, 12), anchor="w")
    
    # Scrollable list
    self.history_frame = ctk.CTkScrollableFrame(
        history_container,
        fg_color="transparent",
        scrollbar_button_color=COLORS["border"],
        scrollbar_button_hover_color=COLORS["text_muted"]
    )
    self.history_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))


def _setup_logging_impl(self):
    """Setup logging with queue handler"""
    class QueueHandler(logging.Handler):
        def __init__(self, log_queue):
            super().__init__()
            self.log_queue = log_queue

        def emit(self, record):
            self.log_queue.put(self.format(record))

    handler = QueueHandler(self.log_queue)
    formatter = logging.Formatter('%(asctime)s │ %(levelname)s │ %(message)s', datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)


def _process_logs_impl(self):
    """Process log queue with color coding"""
    while not self.log_queue.empty():
        msg = self.log_queue.get()
        self.log_text.insert("end", msg + "\n")
        
        if self.autoscroll_var.get():
            self.log_text.see("end")
            
    self.after(100, self.process_logs)


def _update_status_impl(self):
    """Update agent status cards and workflow items"""
    if self.running and hasattr(self, 'ecosystem') and hasattr(self.ecosystem, 'engine'):
        # Update Agent Cards
        for agent_id, card in self.agent_cards.items():
            if agent_id in self.ecosystem.engine.agent_status:
                status = self.ecosystem.engine.agent_status[agent_id].value
                progress = len(self.ecosystem.engine.active_tasks) / 10.0
                card.set_status(status, min(progress, 1.0))
        
        # Update Workflow Items
        for item in self.workflow_items:
            if item.workflow_id and item.workflow_id in self.ecosystem.engine.workflows:
                workflow = self.ecosystem.engine.workflows[item.workflow_id]
                all_tasks = workflow.tasks
                completed = sum(1 for t in all_tasks if t.task_id in self.ecosystem.engine.completed_tasks)
                failed = sum(1 for t in all_tasks if t.task_id in self.ecosystem.engine.failed_tasks)
                
                if failed > 0:
                    item.update_status("failed")
                elif completed == len(all_tasks):
                    item.update_status("completed")
                else:
                    item.update_status("running")

    self.after(1000, self.update_status)


def _start_system_impl(self):
    """Start the agent system"""
    if not self.running:
        self.running = True
        self.system_status_dot.configure(text_color=COLORS["success"])
        self.system_status_text.configure(text="System Online", text_color=COLORS["success"])
        
        # Disable start button, enable stop
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # Start async loop
        threading.Thread(target=self.run_async_loop, daemon=True).start()
        
        logging.info("🚀 ASTRO system started successfully!")
        logging.info("💡 Type a command above to get started")


def _stop_system_impl(self):
    """Stop the agent system"""
    self.running = False
    self.system_status_dot.configure(text_color=COLORS["text_muted"])
    self.system_status_text.configure(text="System Offline", text_color=COLORS["text_muted"])
    
    # Enable start button, disable stop
    self.start_btn.configure(state="normal")
    self.stop_btn.configure(state="disabled")
    
    logging.info("⏹️ System stopped")


def _clear_logs_impl(self):
    """Clear log display"""
    self.log_text.delete("1.0", "end")
    logging.info("🗑️ Logs cleared")


def _run_async_loop_impl(self):
    """Run asyncio loop in background thread"""
    self.loop = asyncio.new_event_loop()
    asyncio.set_event_loop(self.loop)
    
    try:
        # Initialize agents
        self.loop.run_until_complete(self.ecosystem.initialize_agents())
        
        # Create agent cards in main thread
        def create_cards():
            for agent_id, agent in self.ecosystem.agents.items():
                caps = []
                if hasattr(agent, 'capabilities'):
                    caps = [c.value for c in agent.capabilities]
                
                card = AgentCard(self.agents_frame, agent_id, caps)
                card.pack(fill="x", pady=4)
                self.agent_cards[agent_id] = card
        
        self.after(0, create_cards)
        
        # Start engine
        self.loop.create_task(self.ecosystem.engine.start_engine())
        self.loop.create_task(self.ecosystem.dashboard.start_monitoring())
        
        self.loop.run_forever()
    except Exception as e:
        logging.error(f"❌ Engine error: {e}")


def _handle_input_btn_impl(self):
    self.handle_input(None)


def _handle_input_impl(self, event):
    """Handle user input"""
    user_input = self.input_entry.get().strip()
    if not user_input:
        return
        
    self.input_entry.delete(0, "end")
    
    if not self.running:
        messagebox.showwarning("System Offline", "Please click 'Start System' first!")
        return
        
    # Add to history
    time_str = datetime.now().strftime("%H:%M")
    workflow_item = WorkflowItem(self.history_frame, user_input, "running", time_str)
    workflow_item.pack(fill="x", pady=4)
    self.workflow_items.append(workflow_item)
    
    # Process command
    logging.info(f"💬 Command: {user_input}")
    threading.Thread(target=self.process_command, args=(user_input,), daemon=True).start()


def _process_command_impl(self, command):
    """Process command asynchronously"""
    if self.loop:
        asyncio.run_coroutine_threadsafe(_process_command_async_impl(self, command), self.loop)


async def _process_command_async_impl(self, command):
    """Process command with NL interface"""
    # Initialize client if needed
    if not hasattr(self, 'llm_client'):
        self.llm_client = LLMFactory.create_client(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL")
        )
        
    # Initialize NL Interface if needed
    if not hasattr(self, 'nl_interface'):
        self.nl_interface = NaturalLanguageInterface(
            engine=self.ecosystem.engine, 
            llm_client=self.llm_client,
            model_name=os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        )
    
    try:
        workflow_id = await self.nl_interface.process_request(command)
        logging.info(f"✅ Workflow created: {workflow_id}")
    except Exception as e:
        logging.error(f"❌ Error: {e}")


if __name__ == "__main__":
    app = EnhancedGUI()
    app.mainloop()
