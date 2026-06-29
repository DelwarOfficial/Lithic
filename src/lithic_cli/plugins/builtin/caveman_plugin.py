"""Caveman response formatting plugin adapter."""

from __future__ import annotations

from typing import Any

from lithic_cli.plugins import PluginResult, ResponseProvider
from lithic_cli.policy.response_policy import ResponsePolicy


class CavemanPlugin(ResponseProvider):
    """Plugin adapter for Caveman/ResponsePolicy."""
    
    def __init__(self, **config):
        self.config = config
        self._policy = ResponsePolicy()
        
        # Enhanced modes beyond basic ResponsePolicy
        self._extended_modes = {
            "caveman_lite": self._caveman_lite_mode,
            "caveman_full": self._caveman_full_mode, 
            "caveman_ultra": self._caveman_ultra_mode,
            "wenyan_lite": self._wenyan_lite_mode,
            "wenyan_full": self._wenyan_full_mode,
            "technical_brief": self._technical_brief_mode,
            "executive_summary": self._executive_summary_mode
        }
    
    @property
    def name(self) -> str:
        return "caveman"
    
    @property  
    def version(self) -> str:
        return "1.9.0"
    
    def shape_response(self, content: str, mode: str, context: dict[str, Any] = None) -> PluginResult[str]:
        """Shape response content according to mode and context."""
        try:
            context = context or {}
            
            # Use extended modes if available
            if mode in self._extended_modes:
                result = self._extended_modes[mode](content, context)
                return PluginResult.ok(result)
            
            # Fallback to standard ResponsePolicy
            result = self._policy.shape(content, mode)
            return PluginResult.ok(result)
            
        except Exception as e:
            return PluginResult.error(f"Response shaping failed: {e}")
    
    def get_available_modes(self) -> list[str]:
        """Get list of supported response modes."""
        base_modes = ["normal", "concise", "review", "commit", "safety_clear"]
        extended_modes = list(self._extended_modes.keys())
        return base_modes + extended_modes
    
    def _caveman_lite_mode(self, content: str, context: dict[str, Any]) -> str:
        """Light caveman compression - remove filler but keep structure."""
        lines = content.split('\n')
        processed = []
        
        for line in lines:
            # Remove filler words but keep technical terms
            words = line.split()
            filtered = []
            
            filler_words = {'just', 'really', 'basically', 'actually', 'simply', 
                          'certainly', 'of course', 'obviously', 'clearly'}
            
            for word in words:
                if word.lower() not in filler_words:
                    filtered.append(word)
            
            if filtered:
                processed.append(' '.join(filtered))
        
        return '\n'.join(processed)
    
    def _caveman_full_mode(self, content: str, context: dict[str, Any]) -> str:
        """Full caveman compression - drop articles, use fragments."""
        lines = content.split('\n')
        processed = []
        
        for line in lines:
            # More aggressive compression
            words = line.split()
            filtered = []
            
            # Remove articles and filler
            skip_words = {'a', 'an', 'the', 'just', 'really', 'basically', 
                         'actually', 'simply', 'certainly', 'of', 'course', 
                         'obviously', 'clearly', 'that', 'this', 'these', 'those'}
            
            for word in words:
                if word.lower() not in skip_words or len(word) > 4:
                    # Keep longer words even if they're in skip list
                    filtered.append(word)
            
            if filtered:
                processed.append(' '.join(filtered))
        
        # Convert to fragments
        result = '\n'.join(processed)
        
        # Replace verbose phrases with terse equivalents
        replacements = {
            'in order to': 'to',
            'due to the fact that': 'because',
            'it is important to note that': '',
            'please note that': '',
            'it should be noted that': '',
            'first of all': 'first',
            'in conclusion': 'conclusion:',
            'as a result': 'result:',
            'for example': 'e.g.',
            'such as': 'like',
            'in addition': 'also',
            'furthermore': 'also',
            'however': 'but',
            'therefore': 'so',
            'additionally': 'also'
        }
        
        for verbose, terse in replacements.items():
            result = result.replace(verbose, terse)
        
        return result
    
    def _caveman_ultra_mode(self, content: str, context: dict[str, Any]) -> str:
        """Ultra caveman - maximum compression, arrows for causality."""
        result = self._caveman_full_mode(content, context)
        
        # Use arrows and symbols
        result = result.replace(' causes ', ' → ')
        result = result.replace(' leads to ', ' → ')
        result = result.replace(' results in ', ' → ')
        result = result.replace(' because ', ' ← ')
        result = result.replace(' due to ', ' ← ')
        
        # Abbreviate common tech terms (but not code symbols)
        tech_abbrevs = {
            'database': 'DB',
            'configuration': 'config', 
            'authentication': 'auth',
            'authorization': 'authz',
            'request': 'req',
            'response': 'res',
            'function': 'fn',
            'implementation': 'impl',
            'repository': 'repo',
            'environment': 'env',
            'variable': 'var',
            'parameter': 'param'
        }
        
        for full, abbrev in tech_abbrevs.items():
            # Only replace standalone words, not parts of other words
            import re
            pattern = r'\b' + re.escape(full) + r'\b'
            result = re.sub(pattern, abbrev, result, flags=re.IGNORECASE)
        
        return result
    
    def _wenyan_lite_mode(self, content: str, context: dict[str, Any]) -> str:
        """Light classical Chinese style compression.""" 
        # This is a simplified approximation - real wenyan would need proper linguistics
        result = self._caveman_full_mode(content, context)
        
        # Add some classical particles and structure
        result = result.replace('. ', '。')
        result = result.replace('?', '？')
        result = result.replace('!', '！')
        
        return result
    
    def _wenyan_full_mode(self, content: str, context: dict[str, Any]) -> str:
        """Full classical Chinese style (simplified approximation)."""
        result = self._wenyan_lite_mode(content, context)
        
        # More classical transformations (simplified)
        classical_replacements = {
            'is': '者',
            'has': '有', 
            'use': '用',
            'make': '作',
            'get': '得',
            'set': '置',
            'can': '可',
            'will': '將',
            'must': '必'
        }
        
        for eng, classical in classical_replacements.items():
            result = result.replace(f' {eng} ', f' {classical} ')
        
        return result
    
    def _technical_brief_mode(self, content: str, context: dict[str, Any]) -> str:
        """Technical executive brief format."""
        lines = content.split('\n')
        
        # Extract key technical points
        technical_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Prioritize lines with technical content
            if any(term in line.lower() for term in 
                  ['error', 'failed', 'success', 'config', 'api', 'function', 
                   'class', 'method', 'file', 'line', 'bug', 'fix']):
                technical_lines.append(f"• {line}")
            elif len(line) > 20:  # Include substantial content
                technical_lines.append(f"• {line}")
        
        return '\n'.join(technical_lines[:10])  # Limit to top 10 points
    
    def _executive_summary_mode(self, content: str, context: dict[str, Any]) -> str:
        """Executive summary format."""
        lines = content.split('\n')
        
        # Create structured summary
        summary_parts = []
        
        # Status
        if any('error' in line.lower() or 'failed' in line.lower() for line in lines):
            summary_parts.append("**Status:** Issues detected")
        elif any('success' in line.lower() or 'complete' in line.lower() for line in lines):
            summary_parts.append("**Status:** Successful")
        else:
            summary_parts.append("**Status:** In progress")
        
        # Key points (first few substantive lines)
        key_points = []
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 10:
                key_points.append(line)
        
        if key_points:
            summary_parts.append(f"**Key Points:** {'; '.join(key_points[:3])}")
        
        # Action items (lines with action words)
        actions = []
        for line in lines:
            if any(word in line.lower() for word in ['fix', 'update', 'add', 'remove', 'change']):
                actions.append(line.strip())
        
        if actions:
            summary_parts.append(f"**Actions:** {'; '.join(actions[:2])}")
        
        return '\n'.join(summary_parts)
    
    def health_check(self) -> PluginResult[dict[str, Any]]:
        """Check if response formatting is working."""
        try:
            # Test basic functionality
            test_content = "This is a test response that should be formatted correctly."
            test_result = self._policy.shape(test_content, "concise")
            
            return PluginResult.ok({
                "basic_formatting": len(test_result) > 0,
                "available_modes": len(self.get_available_modes()),
                "extended_modes": len(self._extended_modes),
                "config": self.config
            })
        except Exception as e:
            return PluginResult.error(f"Health check failed: {e}")