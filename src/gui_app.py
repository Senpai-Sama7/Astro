"""
ASTRO - Autonomous Agent Ecosystem
Glassmorphic Minimalist GUI - Intuitive for Everyone
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
from utils.model_manager import ModelManager

# Configure CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Glassmorphic Color Palette - Soft, translucent, minimal
COLORS = {
    # Backgrounds - Deep space with subtle transparency feel
    "bg_primary": "#0a0a0f",      # Nearly black
    "bg_glass": "#12121a",        # Glass panel background
    "bg_glass_hover": "#1a1a24",  # Glass hover state
    "bg_input": "#0f0f15",        # Input fields
    
    # Borders - Subtle glow effect
    "border": "#ffffff10",        # Very subtle border
    "border_glow": "#6366f120",   # Accent glow
    
    # Accent - Soft purple/blue gradient feel
    "accent": "#8b5cf6",          # Primary accent (purple)
    "accent_soft": "#6366f1",     # Secondary accent
    "accent_glow": "#8b5cf640",   # Glow effect
    
    # Status colors - Soft, not harsh
    "success": "#10b981",         # Soft green
    "warning": "#f59e0b",         # Soft amber
    "error": "#ef4444",           # Soft red
    "info": "#3b82f6",            # Soft blue
    
    # Text - High contrast but soft
    "text": "#e2e8f0",            # Primary text
    "text_muted": "#64748b",      # Secondary text
    "text_bright": "#f8fafc",     # Bright text
}


class GlassPanel(ctk.CTkFrame):
    """Glassmorphic panel with subtle glow effect"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            fg_color=COLORS["bg_glass"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"]
        )


class AgentCard(ctk.CTkFrame):
    """Minimal agent status indicator"""
    
    def __init__(self, master, agent_id, capabilities, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            fg_color=COLORS["bg_glass"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )
        
        # Friendly names with simple icons
        friendly_names = {
            "research_agent_001": ("🔍", "Research", "Searches the web"),
            "code_agent_001": ("⚡", "Code", "Writes & runs code"), 
            "filesystem_agent_001": ("📄", "Files", "Manages files")
        }
        icon, name, desc = friendly_names.get(agent_id, ("●", agent_id, ""))
        
        # Simple horizontal layout
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=12)
        
        # Icon
        ctk.CTkLabel(
            content, 
            text=icon,
            font=ctk.CTkFont(size=20)
        ).pack(side="left")
        
        # Name and description
        text_frame = ctk.CTkFrame(content, fg_color="transparent")
        text_frame.pack(side="left", padx=12, fill="x", expand=True)
        
        ctk.CTkLabel(
            text_frame, 
            text=name,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_bright"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_frame,
            text=desc,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w")
        
        # Status dot
        self.status_dot = ctk.CTkLabel(
            content, 
            text="●",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        )
        self.status_dot.pack(side="right")
        
    def set_status(self, status, progress=0):
        colors = {
            "idle": COLORS["text_muted"],
            "active": COLORS["success"],
            "busy": COLORS["warning"],
            "failed": COLORS["error"]
        }
        self.status_dot.configure(text_color=colors.get(status.lower(), COLORS["text_muted"]))


class TaskItem(ctk.CTkFrame):
    """Minimal task/workflow item"""
    
    def __init__(self, master, task_name, status, time_str, workflow_id=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            fg_color=COLORS["bg_glass"],
            corner_radius=10,
            height=44
        )
        self.workflow_id = workflow_id
        self.pack_propagate(False)
        
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=14, pady=10)
        
        # Status indicator
        status_colors = {
            "running": COLORS["warning"],
            "completed": COLORS["success"],
            "failed": COLORS["error"],
            "pending": COLORS["text_muted"]
        }
        
        self.status_dot = ctk.CTkLabel(
            content,
            text="●",
            font=ctk.CTkFont(size=8),
            text_color=status_colors.get(status, COLORS["text_muted"])
        )
        self.status_dot.pack(side="left")
        
        # Task name
        ctk.CTkLabel(
            content,
            text=task_name[:40] + "..." if len(task_name) > 40 else task_name,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"]
        ).pack(side="left", padx=10)
        
        # Time
        ctk.CTkLabel(
            content,
            text=time_str,
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"]
        ).pack(side="right")
        
        self.status_colors = status_colors
        
    def update_status(self, status):
        self.status_dot.configure(
            text_color=self.status_colors.get(status, COLORS["text_muted"])
        )


# Alias for backward compatibility
WorkflowItem = TaskItem


class EnhancedGUI(ctk.CTk):
    """Minimalist glassmorphic main window - intuitive for everyone"""
    
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("ASTRO")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.configure(fg_color=COLORS["bg_primary"])
        
        # Initialize state
        self.ecosystem = AutonomousAgentEcosystem()
        self.log_queue = queue.Queue()
        self.agent_cards = {}
        self.workflow_items = []
        self.running = False
        self.loop = None
        
        # Setup logging
        self.setup_logging()
        
        # Simple two-column layout
        self.grid_columnconfigure(0, weight=0)  # Sidebar
        self.grid_columnconfigure(1, weight=1)  # Main
        self.grid_rowconfigure(0, weight=1)

        # Create UI
        self._create_sidebar()
        self._create_main_area()
        
        # Start loops
        self.after(100, self.process_logs)
        self.after(1000, self.update_status)

    def _create_sidebar(self):
        """Minimal glassmorphic sidebar"""
        sidebar = ctk.CTkFrame(
            self, 
            width=280, 
            corner_radius=0, 
            fg_color=COLORS["bg_glass"],
            border_width=1,
            border_color=COLORS["border"]
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        
        # Content container with padding
        content = ctk.CTkFrame(sidebar, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=24)
        
        # Logo - Simple and clean
        ctk.CTkLabel(
            content, 
            text="ASTRO",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_bright"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            content,
            text="Your AI assistant team",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(2, 24))
        
        # Status indicator - Very minimal
        status_frame = ctk.CTkFrame(content, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, 20))
        
        self.system_status_dot = ctk.CTkLabel(
            status_frame, 
            text="●",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"]
        )
        self.system_status_dot.pack(side="left")
        
        self.system_status_text = ctk.CTkLabel(
            status_frame, 
            text="Ready to start",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"]
        )
        self.system_status_text.pack(side="left", padx=(8, 0))
        
        # Single prominent action button
        self.start_btn = ctk.CTkButton(
            content,
            text="Start",
            command=self.start_system,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_soft"],
            height=48,
            corner_radius=12,
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.start_btn.pack(fill="x", pady=(0, 8))
        
        self.stop_btn = ctk.CTkButton(
            content,
            text="Stop",
            command=self.stop_system,
            fg_color="transparent",
            hover_color=COLORS["bg_glass_hover"],
            border_width=1,
            border_color=COLORS["border"],
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"],
            state="disabled"
        )
        self.stop_btn.pack(fill="x", pady=(0, 20))
        
        # Agents section - Compact
        ctk.CTkLabel(
            content,
            text="Agents",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(0, 8))
        
        self.agents_frame = ctk.CTkScrollableFrame(
            content, 
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["text_muted"]
        )
        self.agents_frame.pack(fill="both", expand=True, pady=(0, 16))
        
        # Settings button at bottom - Subtle
        ctk.CTkButton(
            content,
            text="⚙  Settings",
            command=self.open_settings,
            fg_color="transparent",
            hover_color=COLORS["bg_glass_hover"],
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"]
        ).pack(fill="x")

    def _create_main_area(self):
        """Main content area - Clean and focused"""
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)
        
        # Command input - The hero element
        input_card = GlassPanel(main)
        input_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        
        input_content = ctk.CTkFrame(input_card, fg_color="transparent")
        input_content.pack(fill="x", padx=24, pady=20)
        
        # Simple prompt
        ctk.CTkLabel(
            input_content,
            text="What would you like me to do?",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_bright"]
        ).pack(anchor="w", pady=(0, 12))
        
        # Input row
        input_row = ctk.CTkFrame(input_content, fg_color="transparent")
        input_row.pack(fill="x")
        input_row.grid_columnconfigure(0, weight=1)
        
        self.input_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Example: Research the latest AI news and summarize it",
            height=50,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["bg_input"],
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["text_muted"]
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.input_entry.bind("<Return>", self.handle_input)
        
        self.send_btn = ctk.CTkButton(
            input_row,
            text="Go",
            width=80,
            height=50,
            command=self.handle_input_btn,
            corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_soft"],
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.send_btn.grid(row=0, column=1)
        
        # Activity area - Two columns
        activity = ctk.CTkFrame(main, fg_color="transparent")
        activity.grid(row=1, column=0, sticky="nsew")
        activity.grid_columnconfigure(0, weight=2)
        activity.grid_columnconfigure(1, weight=1)
        activity.grid_rowconfigure(0, weight=1)
        
        # Log panel
        log_panel = GlassPanel(activity)
        log_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        
        log_header = ctk.CTkFrame(log_panel, fg_color="transparent")
        log_header.pack(fill="x", padx=20, pady=(16, 8))
        
        ctk.CTkLabel(
            log_header,
            text="Activity",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"]
        ).pack(side="left")
        
        ctk.CTkButton(
            log_header,
            text="Clear",
            command=self.clear_logs,
            fg_color="transparent",
            hover_color=COLORS["bg_glass_hover"],
            width=50,
            height=24,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        ).pack(side="right")
        
        self.log_text = ctk.CTkTextbox(
            log_panel,
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text"],
            font=("SF Mono", 11),
            wrap="word",
            corner_radius=8
        )
        self.log_text.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        
        # Tasks panel
        tasks_panel = GlassPanel(activity)
        tasks_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        
        ctk.CTkLabel(
            tasks_panel,
            text="Tasks",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w", padx=20, pady=(16, 8))
        
        self.history_frame = ctk.CTkScrollableFrame(
            tasks_panel,
            fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["text_muted"]
        )
        self.history_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def open_settings(self):
        """Open settings dialog"""
        if not hasattr(self, 'settings_window') or not self.settings_window.winfo_exists():
            self.settings_window = SettingsDialog(self)
        else:
            self.settings_window.focus()


class SettingsDialog(ctk.CTkToplevel):
    """Intuitive settings with smart model selection"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Settings")
        self.geometry("500x650")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_primary"])
        
        self.transient(parent)
        self.after(150, self._setup_grab)
        
        self.models_cache = {}
        self._build_ui()
        
        self.focus_force()
        self.lift()
        
    def _setup_grab(self):
        try:
            if self.winfo_exists() and self.winfo_viewable():
                self.grab_set()
        except Exception:
            pass
    
    def _build_ui(self):
        """Build intuitive settings UI"""
        # Scrollable content
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=24)
        
        # Title
        ctk.CTkLabel(
            scroll,
            text="Settings",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text_bright"]
        ).pack(anchor="w", pady=(0, 4))
        
        ctk.CTkLabel(
            scroll,
            text="Configure your AI provider and model",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(0, 24))
        
        # === STEP 1: Choose Provider ===
        self._create_section(scroll, "1", "Choose your AI provider", 
            "Select where your AI models come from")
        
        provider_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_glass"], corner_radius=12)
        provider_frame.pack(fill="x", pady=(0, 20))
        
        self.provider_var = ctk.StringVar(value=os.getenv("LLM_PROVIDER", "openai"))
        self.provider_var.trace_add("write", self._on_provider_change)
        
        providers = [
            ("openai", "OpenAI", "GPT-4, GPT-3.5 - Requires API key"),
            ("ollama", "Ollama (Local)", "Free, runs on your computer"),
            ("openrouter", "OpenRouter", "Access many models with one key"),
        ]
        
        for i, (value, name, desc) in enumerate(providers):
            self._create_provider_option(provider_frame, value, name, desc, i == 0)
        
        # === STEP 2: Select Model ===
        self._create_section(scroll, "2", "Select a model", 
            "Choose which AI model to use")
        
        self.model_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_glass"], corner_radius=12)
        self.model_frame.pack(fill="x", pady=(0, 20))
        
        self.model_content = ctk.CTkFrame(self.model_frame, fg_color="transparent")
        self.model_content.pack(fill="x", padx=16, pady=16)
        
        # Model dropdown (will be populated)
        self.model_var = ctk.StringVar(value=os.getenv("LLM_MODEL", "gpt-4o-mini"))
        self.model_dropdown = ctk.CTkOptionMenu(
            self.model_content,
            variable=self.model_var,
            values=["Loading..."],
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_soft"],
            dropdown_fg_color=COLORS["bg_glass"],
            dropdown_hover_color=COLORS["bg_glass_hover"],
            dropdown_text_color=COLORS["text"],
            text_color=COLORS["text"],
            height=44,
            corner_radius=10,
            font=ctk.CTkFont(size=13)
        )
        self.model_dropdown.pack(fill="x")
        
        # Model info label
        self.model_info = ctk.CTkLabel(
            self.model_content,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        )
        self.model_info.pack(anchor="w", pady=(8, 0))
        
        # Ollama-specific: Download section (hidden by default)
        self.ollama_section = ctk.CTkFrame(scroll, fg_color="transparent")
        
        # === STEP 3: API Key (conditional) ===
        self.api_section = ctk.CTkFrame(scroll, fg_color="transparent")
        self.api_section.pack(fill="x")
        
        self._create_section(self.api_section, "3", "Enter your API key", 
            "Required for OpenAI and OpenRouter")
        
        api_frame = ctk.CTkFrame(self.api_section, fg_color=COLORS["bg_glass"], corner_radius=12)
        api_frame.pack(fill="x", pady=(0, 20))
        
        api_content = ctk.CTkFrame(api_frame, fg_color="transparent")
        api_content.pack(fill="x", padx=16, pady=16)
        
        self.api_key_entry = ctk.CTkEntry(
            api_content,
            show="•",
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["text_muted"],
            height=44,
            corner_radius=10,
            placeholder_text="Paste your API key here"
        )
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            self.api_key_entry.insert(0, api_key)
        self.api_key_entry.pack(fill="x")
        
        ctk.CTkLabel(
            api_content,
            text="Your key is stored locally and never shared",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(8, 0))
        
        # === Save Button ===
        ctk.CTkButton(
            scroll,
            text="Save Settings",
            command=self.save_settings,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_soft"],
            text_color=COLORS["text_bright"],
            height=50,
            corner_radius=12,
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(fill="x", pady=(10, 0))
        
        # Load models for current provider
        self._load_models()
    
    def _create_section(self, parent, number, title, subtitle):
        """Create a numbered section header"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 8))
        
        # Number badge
        badge = ctk.CTkLabel(
            frame,
            text=number,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["bg_primary"],
            fg_color=COLORS["accent"],
            corner_radius=12,
            width=24,
            height=24
        )
        badge.pack(side="left")
        
        text_frame = ctk.CTkFrame(frame, fg_color="transparent")
        text_frame.pack(side="left", padx=(10, 0))
        
        ctk.CTkLabel(
            text_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_bright"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_frame,
            text=subtitle,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w")
    
    def _create_provider_option(self, parent, value, name, desc, is_first):
        """Create a provider radio option"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=16, pady=(16 if is_first else 0, 0 if is_first else 16))
        
        radio = ctk.CTkRadioButton(
            frame,
            text="",
            variable=self.provider_var,
            value=value,
            fg_color=COLORS["accent"],
            border_color=COLORS["border"],
            hover_color=COLORS["accent_soft"]
        )
        radio.pack(side="left")
        
        text_frame = ctk.CTkFrame(frame, fg_color="transparent")
        text_frame.pack(side="left", padx=(8, 0), fill="x", expand=True)
        
        ctk.CTkLabel(
            text_frame,
            text=name,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_frame,
            text=desc,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"]
        ).pack(anchor="w")
    
    def _on_provider_change(self, *args):
        """Handle provider change"""
        provider = self.provider_var.get()
        
        # Show/hide API key section
        if provider == "ollama":
            self.api_section.pack_forget()
            self._show_ollama_section()
        else:
            self.ollama_section.pack_forget()
            self.api_section.pack(fill="x")
        
        self._load_models()
    
    def _show_ollama_section(self):
        """Show Ollama-specific options"""
        # Check if Ollama is running
        status = ModelManager.check_ollama_status()
        
        if not status["running"]:
            self.model_info.configure(
                text="⚠️ Ollama not running. Start it first: ollama serve",
                text_color=COLORS["warning"]
            )
    
    def _load_models(self):
        """Load models for current provider"""
        provider = self.provider_var.get()
        
        # Get models
        models = ModelManager.get_models_for_provider(
            provider,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434")
        )
        
        if models:
            model_names = [f"{m.name}" for m in models]
            model_ids = [m.id for m in models]
            self.models_cache = {m.name: m for m in models}
            
            self.model_dropdown.configure(values=model_names)
            
            # Set current model or first available
            current = os.getenv("LLM_MODEL", "")
            if current in model_ids:
                idx = model_ids.index(current)
                self.model_var.set(model_names[idx])
            else:
                self.model_var.set(model_names[0])
            
            # Update info
            self._update_model_info()
        else:
            self.model_dropdown.configure(values=["No models available"])
            self.model_var.set("No models available")
            
            if provider == "ollama":
                self.model_info.configure(
                    text="No models downloaded. Run: ollama pull llama3.2",
                    text_color=COLORS["warning"]
                )
    
    def _update_model_info(self):
        """Update model info label"""
        model_name = self.model_var.get()
        if model_name in self.models_cache:
            model = self.models_cache[model_name]
            info = model.description
            if model.size:
                info += f" • {model.size}"
            self.model_info.configure(text=info, text_color=COLORS["text_muted"])
                     
    def save_settings(self):
        """Save settings"""
        provider = self.provider_var.get()
        os.environ["LLM_PROVIDER"] = provider
        
        # Get model ID from name
        model_name = self.model_var.get()
        if model_name in self.models_cache:
            os.environ["LLM_MODEL"] = self.models_cache[model_name].id
        else:
            os.environ["LLM_MODEL"] = model_name
        
        # API key (only for non-Ollama)
        if provider != "ollama":
            api_key = self.api_key_entry.get()
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
        
        # Set base URL for Ollama
        if provider == "ollama":
            os.environ["LLM_BASE_URL"] = "http://localhost:11434/v1"
        
        # Force re-initialization
        if hasattr(self.parent, 'llm_client'):
            delattr(self.parent, 'llm_client')
        if hasattr(self.parent, 'nl_interface'):
            delattr(self.parent, 'nl_interface')
            
        logging.info(f"✅ Settings saved: {provider} / {os.getenv('LLM_MODEL')}")
        self.destroy()


# Add methods to EnhancedGUI class
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
    """Process log queue"""
    while not self.log_queue.empty():
        msg = self.log_queue.get()
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")  # Always auto-scroll
            
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
        messagebox.showinfo("Start First", "Click the Start button to begin!")
        return
        
    # Add to history
    time_str = datetime.now().strftime("%H:%M")
    task_item = TaskItem(self.history_frame, user_input, "running", time_str)
    task_item.pack(fill="x", pady=4)
    self.workflow_items.append(task_item)
    
    # Process command
    logging.info(f"📝 {user_input}")
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
