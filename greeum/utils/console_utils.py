"""
Console output utilities for cross-platform compatibility
Handles Unicode and emoji output safely across Windows/macOS/Linux
"""

import sys
import platform
from typing import Optional


def safe_print(message: str, file=None, fallback_encoding: str = 'ascii') -> None:
    """
    Safe console output that handles Unicode/emoji across platforms
    
    Args:
        message: Text to output
        file: Output file (default: sys.stdout) 
        fallback_encoding: Encoding to use if UTF-8 fails
    """
    if file is None:
        file = sys.stdout
    
    try:
        # Try direct print first (works on modern systems)
        print(message, file=file)
    except UnicodeEncodeError:
        try:
            # Windows fallback: encode to bytes then decode with errors='replace'
            encoded = message.encode('utf-8', errors='replace')
            safe_message = encoded.decode('utf-8', errors='replace')
            print(safe_message, file=file)
        except:
            # Final fallback: ASCII with emoji/unicode replacement
            safe_message = message.encode(fallback_encoding, errors='replace').decode(fallback_encoding)
            print(safe_message, file=file)


def get_console_encoding() -> str:
    """Get the best encoding for console output"""
    if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
        return sys.stdout.encoding
    return 'utf-8'


def is_unicode_supported() -> bool:
    """Check if current console supports Unicode output"""
    try:
        # Test encoding without actual output
        test_chars = "🚀✅⚠️📊"
        test_chars.encode(sys.stdout.encoding or 'utf-8')
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def configure_windows_console() -> None:
    """Configure Windows console for better Unicode support"""
    if platform.system() == 'Windows':
        try:
            # Try to enable UTF-8 mode on Windows 10+
            import os
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            # For older Windows versions, try cp65001 (UTF-8 codepage)
            import locale
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            except:
                try:
                    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
                except:
                    pass  # Fallback to system default
        except ImportError:
            pass  # Not available, use fallbacks


def emoji_fallback(text: str) -> str:
    """
    Replace emoji with text equivalents for Windows compatibility
    
    Args:
        text: Text containing emoji
        
    Returns:
        Text with emoji replaced by text equivalents
    """
    emoji_map = {
        '🚀': '[INIT]',
        '✅': '[OK]',
        '[ERROR]': '[ERROR]', 
        '⚠️': '[WARNING]',
        '📊': '[STATS]',
        '💾': '[BACKUP]',
        '📦': '[CACHE]',
        '🎯': '[TARGET]',
        '🔍': '[SEARCH]',
        '[MEMORY]': '[MEMORY]',
        '[FAST]': '[FAST]',
        '🏛️': '[LTM]',
        '[PROCESS]': '[PROCESS]',
        '🛡️': '[PROTECTION]',
        '💡': '[TIP]',
        '[SUCCESS]': '[SUCCESS]',
        '🔧': '[CONFIG]',
        '[IMPROVE]': '[IMPROVE]',
        '🧹': '[CLEANUP]'
    }
    
    result = text
    for emoji, replacement in emoji_map.items():
        result = result.replace(emoji, replacement)
    
    return result


class SafeConsole:
    """Safe console output manager"""
    
    def __init__(self):
        self.unicode_supported = is_unicode_supported()
        if platform.system() == 'Windows':
            configure_windows_console()
            
        # Check if verbose output is enabled
        self.verbose = self._check_verbose_mode()
    
    def _check_verbose_mode(self) -> bool:
        """Check if verbose mode is enabled via environment or settings"""
        import os
        
        # Primary check: explicit environment variable
        if os.getenv('GREEUM_VERBOSE', '').lower() in ('1', 'true', 'yes'):
            return True
            
        # Secondary check: verbose flag in CLI context
        if os.getenv('GREEUM_CLI_VERBOSE', '').lower() in ('1', 'true', 'yes'):
            return True
            
        # Default: quiet mode unless explicitly enabled
        return False
    
    def print(self, message: str, file=None) -> None:
        """Print message safely across platforms (only if verbose mode)"""
        if not self.verbose:
            return
            
        if not self.unicode_supported and platform.system() == 'Windows':
            message = emoji_fallback(message)
        
        safe_print(message, file)
    
    def print_status(self, status: str, message: str, file=None) -> None:
        """Print status message with appropriate icon"""
        status_icons = {
            'success': '✅' if self.unicode_supported else '[OK]',
            'error': '[ERROR]' if self.unicode_supported else '[ERROR]',
            'warning': '⚠️' if self.unicode_supported else '[WARNING]',
            'info': '📊' if self.unicode_supported else '[INFO]',
            'process': '[PROCESS]' if self.unicode_supported else '[PROCESS]'
        }
        
        icon = status_icons.get(status, status)
        full_message = f"{icon} {message}"
        self.print(full_message, file)


# Global instance for convenience
console = SafeConsole()


def init_console_safety():
    """Initialize console for safe Unicode output"""
    if platform.system() == 'Windows':
        configure_windows_console()