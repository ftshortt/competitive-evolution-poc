"""EvolvableDeepSeekR1: A wrapper for DeepSeek-R1 reasoning model.

This module implements an evolvable agent wrapper for DeepSeek-R1,
suitable for competitive evolutionary optimization.
"""

import copy
from typing import Dict, Any, Optional
import json


class EvolvableDeepSeekR1:
    """
    Evolvable wrapper for DeepSeek-R1 reasoning model.
    
    Supports get/set/update_weights for evolutionary optimization
    of API configuration parameters.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-reasoner",
        temperature: float = 1.0,
        max_tokens: int = 8000,
        reasoning_effort: str = "medium",
        **kwargs
    ):
        """
        Initialize DeepSeek-R1 agent.
        
        Args:
            api_key: DeepSeek API key
            base_url: API endpoint
            model: Model name (deepseek-reasoner)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            reasoning_effort: low/medium/high for reasoning depth
            **kwargs: Additional API parameters
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.extra_params = kwargs
        
        # Evolvable weights: API configuration parameters
        self._weights = {
            "temperature": temperature,
            "max_tokens": max_tokens,
            "reasoning_effort": reasoning_effort,
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
            "presence_penalty": kwargs.get("presence_penalty", 0.0),
        }

    def get_weights(self) -> Dict[str, Any]:
        """
        Get current evolvable weights (API configuration).
        
        Returns:
            Dictionary of evolvable parameters
        """
        return copy.deepcopy(self._weights)

    def set_weights(self, weights: Dict[str, Any]) -> None:
        """
        Set evolvable weights (API configuration).
        
        Args:
            weights: Dictionary of parameters to update
        """
        self._weights.update(weights)
        # Apply to instance attributes
        if "temperature" in weights:
            self.temperature = weights["temperature"]
        if "max_tokens" in weights:
            self.max_tokens = int(weights["max_tokens"])
        if "reasoning_effort" in weights:
            self.reasoning_effort = weights["reasoning_effort"]

    def update_weights(self, delta: Dict[str, float]) -> None:
        """
        Update weights by delta (for gradient-based evolution).
        
        Args:
            delta: Dictionary of parameter deltas
        """
        for key, value in delta.items():
            if key in self._weights:
                if key == "reasoning_effort":
                    # Handle categorical parameter
                    efforts = ["low", "medium", "high"]
                    current_idx = efforts.index(self._weights[key])
                    new_idx = max(0, min(2, current_idx + int(value)))
                    self._weights[key] = efforts[new_idx]
                elif key == "max_tokens":
                    # Clamp max_tokens to reasonable range
                    self._weights[key] = max(100, min(32000, int(self._weights[key] + value)))
                else:
                    # Numeric parameters with clamping
                    self._weights[key] = max(0.0, min(2.0, self._weights[key] + value))
        
        # Apply updated weights
        self.set_weights(self._weights)

    def reason(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Run DeepSeek-R1 reasoning on the given prompt.
        
        Args:
            prompt: User prompt/query
            system_prompt: Optional system prompt
            
        Returns:
            Dictionary with 'reasoning' and 'response' fields
        """
        # TODO: Implement actual API call to DeepSeek-R1
        # This is a stub implementation for evolutionary framework testing
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Stub response structure
        return {
            "reasoning": f"[R1 reasoning with effort={self.reasoning_effort}]: Analyzing prompt...",
            "response": f"Response using T={self.temperature}, max_tokens={self.max_tokens}",
            "model": self.model,
            "weights": self.get_weights()
        }

    def __call__(self, prompt: str, **kwargs) -> str:
        """
        Make the agent callable for simple inference.
        
        Args:
            prompt: User prompt
            **kwargs: Additional arguments (e.g., system_prompt)
            
        Returns:
            Generated response text
        """
        result = self.reason(prompt, system_prompt=kwargs.get("system_prompt"))
        return result["response"]

    def mutate(self, mutation_rate: float = 0.1) -> 'EvolvableDeepSeekR1':
        """
        Create a mutated copy of this agent.
        
        Args:
            mutation_rate: Probability and magnitude of mutations
            
        Returns:
            New agent with mutated weights
        """
        import random
        
        new_agent = EvolvableDeepSeekR1(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model
        )
        
        new_weights = self.get_weights()
        for key in new_weights:
            if random.random() < mutation_rate:
                if key == "reasoning_effort":
                    efforts = ["low", "medium", "high"]
                    new_weights[key] = random.choice(efforts)
                elif key == "max_tokens":
                    new_weights[key] += random.randint(-1000, 1000)
                else:
                    new_weights[key] += random.gauss(0, mutation_rate)
        
        new_agent.set_weights(new_weights)
        return new_agent

    def save(self, filepath: str) -> None:
        """
        Save agent configuration to file.
        
        Args:
            filepath: Path to save configuration
        """
        config = {
            "model": self.model,
            "base_url": self.base_url,
            "weights": self.get_weights(),
            "extra_params": self.extra_params
        }
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)

    @classmethod
    def load(cls, filepath: str, api_key: Optional[str] = None) -> 'EvolvableDeepSeekR1':
        """
        Load agent configuration from file.
        
        Args:
            filepath: Path to configuration file
            api_key: API key (not saved to file for security)
            
        Returns:
            Loaded agent instance
        """
        with open(filepath, 'r') as f:
            config = json.load(f)
        
        agent = cls(
            api_key=api_key,
            base_url=config.get("base_url", "https://api.deepseek.com/v1"),
            model=config.get("model", "deepseek-reasoner"),
            **config.get("extra_params", {})
        )
        agent.set_weights(config["weights"])
        return agent
