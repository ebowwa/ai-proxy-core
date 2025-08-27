## 0.4.4 - Gemini 2.5 Flash Image support
- Add text-to-image, image edit (image+prompt), and multi-image fusion via unified CompletionClient
- Model availability checks and graceful skips for tests/examples
- Non-breaking response: text in choices[0].message.content; images exposed in response["images"]
- Examples and tests added; README updated

# Changelog

## [0.4.3] - 2025-08-21
### Added
- Universal `system_instruction` abstraction across all providers
  - Automatically converts to provider-specific format (system message for OpenAI/Ollama, parameter for Gemini)
  - Seamless cross-provider compatibility
  - No code changes needed - same parameter works everywhere

### Changed
- CompletionClient now handles system_instruction conversion internally
- OpenAI provider simplified (no longer needs parameter filtering)

## [0.4.2] - 2025-08-21
### Fixed
- Fixed OpenAI provider error with 'system_instruction' parameter (Issue #32)
  - OpenAI provider now properly filters out Gemini-specific parameters
  - Added parameter exclusion for 'system_instruction' and 'safety_settings'
  - Ensures cross-provider compatibility when using unified CompletionClient

## [0.4.1] - 2025-08-19
### Changed
- **BREAKING**: Image generation now requires explicit model selection
- Renamed `GPT4oImageProvider` to `OpenAIImageProvider` for clarity
- Added support for GPT-Image-1 model (available now, not April 2025)
- Removed automatic model fallback - each request must specify the model

### Added
- `ImageModel` enum for explicit model selection (DALLE_2, DALLE_3, GPT_IMAGE_1)
- Model-specific parameter validation
- Token usage tracking for GPT-Image-1
- Support for GPT-Image-1 4K resolution (4096x4096)

### Fixed
- GPT-Image-1 response_format parameter handling
- Model-specific size validation
- Proper error messages for invalid models

## [0.4.0] - 2025-08-19
### Added
- **Image Generation Support**: New GPT4oImageProvider for DALL-E 3 image generation
- Support for multiple image sizes (SQUARE, LANDSCAPE, PORTRAIT)
- Image quality options (STANDARD, HD)
- Style options (VIVID, NATURAL)
- Image editing capabilities with optional masks
- Azure OpenAI image generation support
- Localized image generation for app internationalization
- C2PA metadata extraction for AI-generated content authenticity
- Comprehensive test suite for image generation

### Changed
- Updated package structure to include image providers
- Enhanced README with image generation examples

### Technical
- Abstract provider pattern for future image generation services
- Integration with existing BaseCompletions architecture
- Full compatibility with uv package manager

## [0.3.9] - 2025-08-09
- Version bump for PyPI release

## [0.3.8] - 2025-08-09
- Add `/api/models` endpoint for listing available models
- Fix GoogleCompletions to query actual Google Gemini API for model list (60+ models!)
- Make list_models() async to properly query provider APIs
- Fix ModelManager fallback logic when no providers are registered
- Improve CompletionClient to handle both sync and async list_models methods
- Update .env.example with comprehensive configuration options
- Add support for filtering models by provider (`/api/models?provider=gemini`)

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
