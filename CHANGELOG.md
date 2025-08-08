# Changelog

## [0.3.7] - 2025-08-08
- Restructure project: Move ai_proxy_core source to src/ directory
- Rename api_demo to api_layer for clarity
- Update documentation to use uv run instead of python
- Remove backup file gemini_live_backup.py.old
- Organize test files into tests/ directory
- Create setup/ directory for build artifacts
- Maintain package name as ai_proxy_core for PyPI compatibility

## [0.3.6] - 2025-08-08
- Remove legacy completions.py file (replaced by completion_client.py)
- Remove deprecated CompletionsHandler export
- Rename api folder to api_layer to clarify it's the API layer
- Clean up redundant code while maintaining full functionality
- Verified Gemini works with modern CompletionClient

## [0.3.5] - 2025-08-08
- Clean up WebSocket file redundancies
- Remove duplicate gemini_live_fixed.py file
- Archive backup WebSocket implementation
- Organize debug and test files into debug/ folder
- Maintain full WebSocket functionality while reducing code duplication
- Tested and verified all endpoints working correctly

## [0.3.4] - 2025-08-08
- Fix GoogleCompletions message format handling for google-genai library
- Convert complex message formats to simple string prompts for compatibility
- Fix message parsing to handle both string and list content types
- Improve error handling for API responses
- Ensure proper text extraction from structured message content

## [0.3.3] - 2025-08-04
- Fix Gemini Live WebSocket implementation
- Implement proper async context manager handling for sessions
- Add bidirectional communication with separate async tasks
- Fix message format compatibility between client and server
- Add HTML demos for Gemini Live WebSocket (examples/gemini_live_demo.html)
- Add debug tools for testing WebSocket connections
- Reorganize test files into proper directories
- Note: Audio input pending (requires PCM format conversion from WebM)

## [0.3.2] - 2025-08-04
- Add security scaffolding for future implementation
- Add optional `use_secure_storage` parameter to providers (GoogleCompletions, OpenAICompletions)
- Add security dependencies to setup.py extras (`[security]`, `[vault]`, `[aws]`)
- Add TODO placeholders for authentication and secure key storage implementation
- Update CompletionClient to support secure storage configuration
- Maintain full backward compatibility - no breaking changes
- Related to issues #19 and #20

## [0.3.1] - 2025-08-03
- Fix telemetry NoOpTelemetry missing request_counter attribute
- Resolve GitHub issues #15, #16, #17
- Add LLM prompt reference for easy integration help
- Add AI Proxy Core expert agent for Claude
- Add roadmap link to README

## [0.3.0] - 2025-08-03
- Introduce CompletionClient unified interface
- Add model management system with ModelManager
- Implement model discovery and automatic provider detection

## [0.2.0] - 2025-08-03
- Major refactor to provider architecture
- Add support for multiple LLM providers simultaneously

## [0.1.9.0] - 2025-08-03
- API migration to provider architecture completed
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