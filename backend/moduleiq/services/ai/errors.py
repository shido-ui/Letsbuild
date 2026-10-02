class AIProviderError(RuntimeError): pass
class InvalidCredentialError(AIProviderError): pass
class ProviderTimeoutError(AIProviderError): pass
class ProviderUnavailableError(AIProviderError): pass
