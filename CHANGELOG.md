# Changelog

## [0.1.9] - 2025-08-02
- BREAKING: Refactor to provider-specific classes (GoogleCompletions, OpenAICompletions, OllamaCompletions)
- Add multi-provider support with clean separation
- Add optional OpenTelemetry support for basic observability
- Track request counts by model/status across all providers
- Track session duration for WebSocket connections
- Add OpenAI-compatible endpoint support (Groq, Anyscale, etc.)
- Deprecate CompletionsHandler in favor of provider-specific classes
- Add optional dependencies for different providers

## [0.1.8] - 2025-08-02
- Add built-in tool support (code_execution, google_search) for Gemini Live
- Add custom_tools parameter for user-defined function declarations
- Update README with comprehensive tool examples
- Add release.sh script for automated releases

## [0.1.7] - 2025-08-02
- (Previous release - changes not documented)

## [0.1.6] - 2025-01-31
- Add system instruction support for Gemini Live
- Improve WebSocket response handling
- Add TEXT modality to default config

## [0.1.5] - 2025-01-30
- Refactor to Python package structure
- Add ai_proxy_core module

## [0.1.0] - 2025-01-29
- Initial release
- Basic Gemini completions handler
- Gemini Live WebSocket support