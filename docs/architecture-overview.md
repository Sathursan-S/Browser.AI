# Browser.AI Architecture Overview

## Introduction

Browser.AI is a sophisticated browser automation framework that makes websites accessible for AI agents. It combines AI-powered decision-making with robust browser automation capabilities through a modular architecture built on top of Playwright.

## High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[User Interface]
        API[API Interface]
    end
    
    subgraph "Core Browser.AI Framework"
        Agent[AI Agent Service]
        Controller[Action Controller]
        Browser[Browser Service]
        DOM[DOM Processing Service]
    end
    
    subgraph "External Services"
        LLM[Language Models<br/>OpenAI, Anthropic, Ollama, etc.]
        PW[Playwright Browser Engine]
        Web[Target Websites]
    end
    
    UI --> Agent
    API --> Agent
    Agent --> Controller
    Agent --> LLM
    Controller --> Browser
    Browser --> DOM
    Browser --> PW
    PW --> Web
    DOM --> PW
    
    style Agent fill:#e1f5fe
    style Controller fill:#f3e5f5
    style Browser fill:#e8f5e8
    style DOM fill:#fff3e0
```

## Component Architecture

### 1. AI Agent Service (`browser_ai.agent`)

The central orchestrator that coordinates all browser automation tasks using AI decision-making.

```mermaid
graph LR
    subgraph "Agent Service"
        AS[Agent Service]
        MM[Message Manager]
        Prompts[System Prompts]
        Views[Agent Views]
    end
    
    subgraph "External Dependencies"
        LC[LangChain LLMs]
        Obs[LMNR Observability]
    end
    
    AS --> MM
    AS --> Prompts
    AS --> Views
    AS --> LC
    AS --> Obs
    
    style AS fill:#e1f5fe
```

**Key Responsibilities:**
- Task planning and execution orchestration
- LLM integration and prompt management
- Step-by-step action decision making
- Error handling and retry logic
- Conversation state management
- Vision capabilities for screenshot analysis

### 2. Action Controller (`browser_ai.controller`)

Manages the execution of browser actions through a registry pattern.

```mermaid
graph LR
    subgraph "Controller System"
        Ctrl[Controller]
        Reg[Action Registry]
        Actions[Available Actions]
    end
    
    subgraph "Action Types"
        Click[Click Element]
        Nav[Navigate/GoTo]
        Input[Text Input]
        Scroll[Scroll Actions]
        Tab[Tab Management]
        Search[Google Search]
        Done[Task Completion]
    end
    
    Ctrl --> Reg
    Reg --> Actions
    Actions --> Click
    Actions --> Nav
    Actions --> Input
    Actions --> Scroll
    Actions --> Tab
    Actions --> Search
    Actions --> Done
    
    style Ctrl fill:#f3e5f5
```

**Key Features:**
- Decorator-based action registration
- Type-safe action parameters using Pydantic
- Extensible action system
- Action exclusion capabilities
- Async execution support

### 3. Browser Service (`browser_ai.browser`)

Enhanced Playwright wrapper providing advanced browser management capabilities.

```mermaid
graph TB
    subgraph "Browser Management"
        BC[Browser Config]
        B[Browser Service]
        BCtx[Browser Context]
    end
    
    subgraph "Playwright Integration"
        PW[Playwright Browser]
        Page[Page Instance]
        CDP[Chrome DevTools Protocol]
    end
    
    BC --> B
    B --> BCtx
    B --> PW
    BCtx --> Page
    PW --> CDP
    
    style B fill:#e8f5e8
```

**Configuration Options:**
- Headless/headed mode control
- Security settings management
- Custom Chrome arguments
- WebSocket/CDP connection support
- Proxy configuration
- User agent customization

### 4. DOM Processing Service (`browser_ai.dom`)

Sophisticated DOM analysis and element extraction system.

```mermaid
graph TB
    subgraph "DOM Processing"
        DS[DOM Service]
        Builder[DOM Tree Builder]
        HTP[History Tree Processor]
    end
    
    subgraph "Element Analysis"
        Extract[Element Extraction]
        Highlight[Element Highlighting]
        Viewport[Viewport Analysis]
        Coords[Coordinate Mapping]
    end
    
    subgraph "JavaScript Engine"
        JS[buildDomTree.js]
        Eval[Page Evaluation]
    end
    
    DS --> Builder
    DS --> HTP
    Builder --> Extract
    Builder --> Highlight
    Extract --> Viewport
    Extract --> Coords
    DS --> JS
    JS --> Eval
    
    style DS fill:#fff3e0
```

**Key Capabilities:**
- Interactive element identification
- Smart element highlighting
- Viewport-aware element extraction
- XPath and CSS selector generation
- Element history tracking
- Shadow DOM support

## Data Flow Architecture

### Task Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant Controller
    participant Browser
    participant DOM
    participant LLM
    participant Website
    
    User->>Agent: Submit Task
    Agent->>LLM: Generate Plan
    LLM-->>Agent: Task Steps
    
    loop For Each Step
        Agent->>Browser: Get Current State
        Browser->>DOM: Extract Elements
        DOM->>Website: Analyze DOM
        Website-->>DOM: DOM Tree
        DOM-->>Browser: Processed Elements
        Browser-->>Agent: Browser State
        
        Agent->>LLM: Decide Next Action
        LLM-->>Agent: Action Decision
        
        Agent->>Controller: Execute Action
        Controller->>Browser: Perform Action
        Browser->>Website: Browser Command
        Website-->>Browser: State Update
        Browser-->>Controller: Action Result
        Controller-->>Agent: Execution Result
    end
    
    Agent-->>User: Task Complete
```

### DOM Processing Workflow

```mermaid
graph TD
    Start[Page Load] --> Inject[Inject JavaScript]
    Inject --> Build[Build DOM Tree]
    Build --> Filter[Filter Interactive Elements]
    Filter --> Highlight[Highlight Elements]
    Highlight --> Extract[Extract Coordinates]
    Extract --> Map[Create Selector Map]
    Map --> Return[Return DOM State]
    
    subgraph "Element Processing"
        Build --> Traverse[Traverse DOM]
        Traverse --> Check[Check Visibility]
        Check --> Attr[Extract Attributes]
        Attr --> Pos[Calculate Positions]
        Pos --> Filter
    end
    
    style Start fill:#e8f5e8
    style Return fill:#e8f5e8
```

## Integration Points

### Language Model Integration

Browser.AI supports multiple LLM providers through LangChain:

- **OpenAI** (GPT-3.5, GPT-4, GPT-4V)
- **Anthropic** (Claude family)
- **Google** (Gemini family)
- **Ollama** (Local models)
- **Fireworks** (Fast inference)
- **AWS Bedrock** (Enterprise)

### Browser Engine Integration

Built on Playwright for cross-browser support:
- Chromium-based browsers
- Firefox
- WebKit (Safari)

### Observability Integration

- **LMNR** - Performance monitoring and debugging
- **Structured logging** - Comprehensive operation tracking
- **Conversation persistence** - Chat history management

## Configuration Management

### Environment Configuration

```bash
# LLM API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Logging Configuration
BROWSER_AI_LOGGING_LEVEL=info  # result | debug | info
```

### Browser Configuration

```python
from browser_ai import BrowserConfig

config = BrowserConfig(
    headless=False,
    disable_security=True,
    extra_chromium_args=['--no-sandbox'],
    chrome_instance_path='/path/to/chrome'
)
```

## Scalability and Performance

### Async Architecture
- Full async/await support throughout the stack
- Concurrent action execution capabilities
- Non-blocking LLM communication

### Memory Management
- Automatic garbage collection for browser resources
- DOM tree caching with smart invalidation
- Message history size limits

### Error Handling
- Comprehensive retry mechanisms
- Graceful degradation for LLM failures
- Browser crash recovery

## Security Considerations

### Data Protection
- Sensitive data masking in logs
- Secure API key management
- No data persistence by default

### Browser Security
- Configurable security settings
- Sandbox environment support
- User agent rotation capabilities

---

*This architecture overview provides the foundation for understanding Browser.AI's modular design and integration capabilities. For detailed implementation guides, refer to the component-specific documentation.*