"""Telegram bot integration for ASTRO."""

import os
from typing import Optional, Callable

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        filters,
        ContextTypes
    )
    HAS_TELEGRAM = True
except ImportError:
    HAS_TELEGRAM = False
    Update = None
    ContextTypes = None


class TelegramBot:
    """Telegram bot for controlling ASTRO via messaging."""
    
    def __init__(
        self,
        token: Optional[str] = None,
        allowed_users: Optional[list] = None,
        skill_manager=None,
        llm_provider=None
    ):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.allowed_users = set(allowed_users or [])
        self.skill_manager = skill_manager
        self.llm_provider = llm_provider
        
        self.application: Optional['Application'] = None
        self._running = False
        self._message_handler: Optional[Callable] = None
    
    def is_available(self) -> bool:
        """Check if Telegram bot is available."""
        return HAS_TELEGRAM and self.token is not None
    
    async def start(self):
        """Start the Telegram bot."""
        if not HAS_TELEGRAM:
            raise ImportError("python-telegram-bot required. Run: pip install python-telegram-bot")
        
        if not self.token:
            raise ValueError("Telegram bot token required. Set TELEGRAM_BOT_TOKEN env var.")
        
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        self.application.add_handler(CommandHandler("skills", self._cmd_skills))
        self.application.add_handler(CommandHandler("canvas", self._cmd_canvas))
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Start bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        self._running = True
        print("Telegram bot started")
    
    async def stop(self):
        """Stop the Telegram bot."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        self._running = False
    
    def set_message_handler(self, handler: Callable[[str, str, Callable], None]):
        """Set handler for incoming messages.
        
        Args:
            handler: Function(user_id, message, reply_func)
        """
        self._message_handler = handler
    
    def _check_auth(self, user_id: int) -> bool:
        """Check if user is authorized."""
        if not self.allowed_users:
            return True
        return str(user_id) in self.allowed_users
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        
        if not self._check_auth(user.id):
            await update.message.reply_text("⛔ You are not authorized to use this bot.")
            return
        
        welcome_text = f"""👋 Hello {user.first_name}!

I'm ASTRO, your AI assistant. You can control me through Telegram!

📝 **Commands:**
/skills - List available skills
/canvas - Create a live canvas
/help - Show help

💬 Just send me a message and I'll help you out!
"""
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """🤖 **ASTRO Bot Help**

**Natural Language:**
Just type what you want me to do!
• "Run my tests"
• "Show me files in the project"
• "Create a summary of my changes"

**Skills:**
Use /skills to see what I can do

**Canvas:**
Use /canvas to create a visual workspace

**Tips:**
• I can execute skills directly
• I remember our conversation context
• Send documents for me to analyze
"""
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def _cmd_skills(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /skills command."""
        if not self.skill_manager:
            await update.message.reply_text("⚠️ Skill manager not available")
            return
        
        skills = self.skill_manager.registry.list_skills()
        
        if not skills:
            await update.message.reply_text("No skills available")
            return
        
        # Create inline keyboard with skill buttons
        keyboard = []
        for skill in skills[:10]:  # Limit to first 10
            keyboard.append([InlineKeyboardButton(
                f"{skill['icon']} {skill['name']}",
                callback_data=f"skill_info:{skill['name']}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📦 **Available Skills:**\nTap to learn more",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def _cmd_canvas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /canvas command."""
        # Create a new canvas
        from ..canvas import CanvasManager
        
        canvas_manager = CanvasManager()
        canvas = canvas_manager.create(title="Telegram Canvas")
        
        await update.message.reply_text(
            f"🎨 **Canvas Created!**\n\n"
            f"ID: `{canvas.id}`\n"
            f"Open in browser: http://localhost:5000/canvas/{canvas.id}",
            parse_mode="Markdown"
        )
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("skill_info:"):
            skill_name = data.split(":")[1]
            help_text = self.skill_manager.get_skill_help(skill_name)
            await query.edit_message_text(help_text, parse_mode="Markdown")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages."""
        user = update.effective_user
        
        if not self._check_auth(user.id):
            await update.message.reply_text("⛔ Not authorized")
            return
        
        message_text = update.message.text
        
        # Send "thinking" indicator
        thinking_msg = await update.message.reply_text("🤔 Thinking...")
        
        try:
            # Process through handler if set
            if self._message_handler:
                async def reply(text: str):
                    await thinking_msg.edit_text(text, parse_mode="Markdown")
                
                await self._message_handler(str(user.id), message_text, reply)
            else:
                # Default: try to use LLM
                if self.llm_provider:
                    response = await self.llm_provider.complete([
                        {"role": "user", "content": message_text}
                    ])
                    await thinking_msg.edit_text(response.content)
                else:
                    await thinking_msg.edit_text("⚠️ No message handler configured")
        
        except Exception as e:
            await thinking_msg.edit_text(f"❌ Error: {e}")
    
    async def send_message(self, user_id: str, text: str):
        """Send message to user."""
        if self.application:
            await self.application.bot.send_message(
                chat_id=int(user_id),
                text=text,
                parse_mode="Markdown"
            )
