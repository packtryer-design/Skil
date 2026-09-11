# Prompt Architect --- Capability-Aware Runtime Extension

## Purpose

This extension adds **Capability Discovery, Runtime Analysis, Tool Gap
Analysis, and Compatibility Validation** to the Prompt Architect.

The goal is to ensure that every generated Prompt or Skill is compatible
with the **actual model and execution environment** it is intended for.

The Prompt Architect should not assume that a model has a tool,
integration, modality, context window, execution ability, or external
access merely because the generated task would benefit from it.

> **Determine what the target model and runtime can actually do before
> compiling the final Prompt or Skill.**

This extension complements the existing Prompt Architect plan rather
than replacing its existing stages.

------------------------------------------------------------------------

# 1. Core Principle

Prompt Architect should optimize for:

> **Capability-aware task completion.**

A generated Prompt or Skill must distinguish between:

1.  What the model itself can do.
2.  What the runtime can provide.
3.  What tools are currently available.
4.  What integrations are connected.
5.  What resources are accessible.
6.  What capabilities are unavailable.
7.  What capabilities are required by the requested task.
8.  What missing capabilities could potentially be added.
9.  What limitations cannot reasonably be removed.

The Architect must never generate instructions that falsely imply
unavailable capabilities.

------------------------------------------------------------------------

# 2. Model-Agnostic Architecture

The system should support multiple model/runtime combinations.

``` text
                         USER REQUEST
                              |
                              v
                       TASK ANALYSIS
                              |
                              v
                  TARGET MODEL IDENTIFICATION
                              |
                              v
                    CAPABILITY DISCOVERY
                +-------------+-------------+
                |             |             |
                v             v             v
           User Input     Model Research   Runtime
                                             Inspection
                |             |             |
                +-------------+-------------+
                              |
                              v
                     CAPABILITY PROFILE
                              |
                              v
                   REQUIREMENT MAPPING
                              |
                              v
                      GAP ANALYSIS
                              |
                    +---------+---------+
                    |                   |
                    v                   v
              No Critical Gap      Capability Gap
                    |                   |
                    |                   v
                    |             Tool / Integration
                    |              Recommendations
                    |                   |
                    +---------+---------+
                              |
                              v
                    COMPATIBILITY CHECK
                              |
                              v
                    PROMPT / SKILL IR
                              |
                              v
                       COMPILATION
                              |
                              v
                    FINAL PROMPT / SKILL
```

Targets may include:

-   Claude
-   Local Qwen
-   Local Llama
-   Local Kimi
-   OpenAI-compatible local models
-   Models accessed through Open WebUI
-   Models accessed through custom applications
-   Models accessed through APIs
-   Agent runtimes
-   MCP-enabled environments
-   Future model ecosystems

------------------------------------------------------------------------

# 3. Runtime Is Separate From Model

A critical distinction is:

> **Model capability is not the same thing as runtime capability.**

A model may support tool calling while the runtime provides no tools.

A model may generate Python while the runtime cannot execute Python.

Therefore the Capability Profile must represent the model and runtime
separately.

``` text
MODEL:
Can reason about Python
Can generate Python
Can potentially request tool calls

RUNTIME:
No Python execution
No filesystem
No database

RESULT:
The model can produce Python code,
but cannot honestly claim that the code was executed.
```

------------------------------------------------------------------------

# 4. Capability Profile

Add a first-class internal structure:

``` text
CAPABILITY_PROFILE
```

Conceptually:

``` text
CAPABILITY_PROFILE

MODEL
    provider
    name
    version
    modality
    reasoning_capability
    context_window
    output_limits
    structured_output
    tool_calling
    vision
    audio_input
    audio_output
    video_input
    video_output
    code_generation
    instruction_following

RUNTIME
    platform
    application
    agent_framework
    execution_environment
    sandbox
    operating_system
    network_access

TOOLS
    filesystem
    terminal
    python
    shell
    browser
    web
    database
    git
    image_generation
    image_analysis
    audio
    video
    document_processing
    spreadsheet_processing
    code_execution

INTEGRATIONS
    MCP
    plugins
    APIs
    cloud_services
    storage
    databases
    external_services

RESOURCES
    files
    folders
    repositories
    documents
    databases
    APIs
    credentials
    mounted_storage

LIMITATIONS
    unavailable_tools
    context_limits
    format_limits
    execution_limits
    network_limits
    permission_limits
    model_limits

CONFIDENCE
    confirmed
    inferred
    researched
    unknown
```

------------------------------------------------------------------------

# 5. Capability Discovery

Before compiling a complex Prompt or Skill, determine the capabilities
of the target environment.

Use this hierarchy:

``` text
1. Known runtime information
        |
2. Direct environment inspection
        |
3. Connected tool inspection
        |
4. Model/runtime documentation research
        |
5. User clarification
        |
6. Safe assumption
```

Prefer reliable evidence over assumptions.

------------------------------------------------------------------------

# 6. Target Identification

Determine the target whenever relevant.

Possible target declarations:

``` text
TARGET_MODEL
TARGET_RUNTIME
TARGET_APPLICATION
TARGET_AGENT
TARGET_ENVIRONMENT
```

Example:

``` text
Target model:
Qwen

Runtime:
Local Open WebUI

Execution:
Local Linux machine

Tools:
Filesystem + Python

Network:
Disabled
```

If target information materially affects the result, ask a minimal
clarification question.

------------------------------------------------------------------------

# 7. Research Before Compilation

Prompt Architect should be able to research the target model/runtime
when reliable information is not already available.

Research may determine:

-   Supported modalities.
-   Context window.
-   Tool-calling support.
-   Structured output support.
-   Reasoning behavior.
-   Vision support.
-   Audio support.
-   Known execution limitations.
-   Model-specific instruction behavior.
-   Supported integrations.
-   Official runtime capabilities.
-   Version-specific changes.

Prefer:

1.  Official model documentation.
2.  Official runtime documentation.
3.  Official API documentation.
4.  Official repositories/documentation.
5.  High-quality technical references.
6.  Community information only when necessary.

Distinguish:

``` text
CONFIRMED BY DOCUMENTATION
INFERRED
UNKNOWN
```

------------------------------------------------------------------------

# 8. Research Confidence

Every researched capability should have a confidence level:

``` text
CONFIRMED
HIGH CONFIDENCE
MEDIUM CONFIDENCE
LOW CONFIDENCE
UNKNOWN
```

Important capabilities should retain their evidence source internally.

------------------------------------------------------------------------

# 9. User Capability Questions

Ask the user only when necessary.

Examples:

> Can this local model execute Python, or can it only generate Python
> code?

> Does your Open WebUI instance expose local files to the model?

> Can this runtime make outbound web requests?

Follow the existing clarification principle:

> **Ask the minimum number of questions that materially improve the
> outcome.**

Do not ask for information that can be reliably discovered through
inspection or research.

------------------------------------------------------------------------

# 10. Capability Question Prioritization

Prioritize questions by impact.

### Priority 1 --- Blocking capabilities

Capabilities without which the requested task cannot be completed.

### Priority 2 --- Major quality capabilities

Capabilities that significantly affect reliability or quality.

Examples:

-   Vision for image-heavy document analysis.
-   Larger context for very large repositories.
-   Web access for current research.

### Priority 3 --- Optimization capabilities

Capabilities that improve convenience but are not required.

Examples:

-   Git integration.
-   Additional visualization libraries.
-   Optional browser automation.

------------------------------------------------------------------------

# 11. Required Capability Profile

Create a second structure:

``` text
REQUIRED_CAPABILITY_PROFILE
```

This describes what the requested task needs.

Example:

``` text
FILESYSTEM:
    required

PYTHON:
    required

WEB:
    optional

DATABASE:
    optional

VISION:
    recommended

GIT:
    optional
```

It should be derived from task requirements and workflow.

------------------------------------------------------------------------

# 12. Capability Matching

Compare:

``` text
ACTUAL CAPABILITIES
        VS
REQUIRED CAPABILITIES
```

Possible results:

``` text
FULLY_COMPATIBLE
COMPATIBLE_WITH_LIMITATIONS
REQUIRES_OPTIONAL_CAPABILITIES
REQUIRES_ADDITIONAL_TOOLS
NOT_CURRENTLY_EXECUTABLE
UNKNOWN
```

------------------------------------------------------------------------

# 13. Tool Gap Analysis

Add:

``` text
TOOL GAP ANALYSIS
```

Its purpose is to identify missing capabilities between task
requirements and the runtime.

For each gap determine:

``` text
CAPABILITY
STATUS
IMPORTANCE
POSSIBLE SOLUTION
INSTALLABLE?
CONFIGURABLE?
SUBSTITUTABLE?
WORKAROUND?
```

------------------------------------------------------------------------

# 14. Tool Recommendation System

When a missing capability can be added, recommend it.

Example:

``` text
Missing capability:
Python execution

Importance:
Required

Possible solution:
Add Python execution tool

Alternative:
Generate Python code for manual execution

Status:
Current task cannot be fully autonomous without execution
```

Never imply that a recommended tool has already been installed or
enabled.

------------------------------------------------------------------------

# 15. Tool Addition Modes

Distinguish:

``` text
REQUIRED
RECOMMENDED
OPTIONAL
ALTERNATIVE
```

Example:

``` text
Required:
Filesystem access

Recommended:
Python execution

Optional:
Git integration

Alternative:
User manually runs generated scripts
```

------------------------------------------------------------------------

# 16. Installability and Configurability

A missing capability may be:

``` text
AVAILABLE
AVAILABLE_BUT_DISABLED
CONFIGURABLE
INSTALLABLE
REQUIRES_EXTERNAL_SERVICE
REQUIRES_RUNTIME_CHANGE
NOT_SUPPORTED
UNKNOWN
```

This distinguishes a missing tool from a missing model capability.

------------------------------------------------------------------------

# 17. Capability Substitution

When a required capability is unavailable, determine whether another
workflow can achieve the same objective.

Example:

``` text
Required:
Web research

Unavailable:
Web access

Possible substitution:
User supplies URLs/documents

Result:
Task remains possible with reduced autonomy
```

Another:

``` text
Required:
Python execution

Unavailable:
Python

Possible substitution:
Generate executable code for the user

Result:
Task becomes advisory rather than executable
```

The Architect should explicitly state when a substitution changes the
operating mode.

------------------------------------------------------------------------

# 18. Capability-Aware Operating Mode

Operating mode must be constrained by actual capabilities.

``` text
Requested mode:
EXECUTOR

Required:
Filesystem + terminal

Actual:
Filesystem only

Result:
Cannot operate as full EXECUTOR.

Possible mode:
ANALYST / ADVISOR

Alternative:
Add terminal capability.
```

Do not fake autonomy.

------------------------------------------------------------------------

# 19. Capability-Aware Autonomy

Autonomy levels should depend on available execution capabilities.

``` text
A0:
Explain only

A1:
Recommend

A2:
Plan

A3:
Execute with checkpoints

A4:
Execute autonomously within boundaries
```

A3/A4 require appropriate tools, permissions, and verification.

> **Autonomy must never exceed the capabilities and permissions of the
> runtime.**

------------------------------------------------------------------------

# 20. Tool Rules Compilation

For each available tool determine:

``` text
WHEN TO USE
WHEN NOT TO USE
WHAT TO INSPECT
WHAT EVIDENCE TO COLLECT
WHAT ACTIONS ARE ALLOWED
WHAT ACTIONS REQUIRE CONFIRMATION
WHAT TO REPORT
```

The generated artifact must reference only tools actually available to
the target.

------------------------------------------------------------------------

# 21. No-Fake-Capability Rule

This is mandatory.

Do not generate:

``` text
"Use the browser to..."
```

when no browser exists.

Do not generate:

``` text
"Run the code and verify the result."
```

when execution is unavailable.

Do not generate:

``` text
"Search the internet..."
```

when web access is unavailable.

Do not generate:

``` text
"Edit the file directly..."
```

when the runtime cannot modify files.

Instead use capability-aware fallbacks.

------------------------------------------------------------------------

# 22. Evidence-Aware Execution

Generated artifacts should distinguish:

``` text
CAN DO
DID DO
OBSERVED
INFERRED
GENERATED
NOT VERIFIED
```

Example:

``` text
Generated:
Python script

Executed:
No

Verified:
No
```

This prevents false execution claims.

------------------------------------------------------------------------

# 23. Context Window Analysis

Capability discovery should include context limits.

Estimate:

``` text
Task context
+
Resource context
+
Prompt size
+
Expected output
```

Compare with the target model's usable context.

If too large, recommend:

-   Chunking.
-   Retrieval.
-   Summarization.
-   Hierarchical processing.
-   File-based workflows.
-   External memory.
-   RAG.
-   Multi-pass analysis.

------------------------------------------------------------------------

# 24. Modality Compatibility

Account for:

``` text
VISION
AUDIO
VIDEO
TEXT
IMAGE GENERATION
STRUCTURED OUTPUT
```

If a task requires image interpretation but the model has no vision:

``` text
Compatibility:
INCOMPATIBLE

Possible solutions:
1. Use a vision-capable model.
2. Add an image-analysis service.
3. Convert image information into text externally.
```

------------------------------------------------------------------------

# 25. Resource Accessibility

A resource existing on the user's machine does not mean the model can
access it.

Distinguish:

``` text
RESOURCE EXISTS
RESOURCE ACCESSIBLE
RESOURCE MODIFIABLE
RESOURCE EXECUTABLE
```

Example:

``` text
File:
C:/project/data.xlsx

Exists:
YES

Accessible:
NO

Writable:
NO

Result:
Capability gap
```

------------------------------------------------------------------------

# 26. Permissions

Represent permissions explicitly:

``` text
READ
WRITE
EXECUTE
DELETE
NETWORK
DATABASE_READ
DATABASE_WRITE
ADMIN
```

A tool being available does not imply every action is permitted.

------------------------------------------------------------------------

# 27. Local Model Support

Local models are first-class targets.

Example:

``` text
LOCAL MODEL

Model:
Qwen

Runtime:
Open WebUI

Tools:
Filesystem
Python

Integrations:
None

Network:
Disabled
```

The absence of plugins does not prevent Prompt Architect from working.

The Capability Profile simply reflects the actual local runtime.

------------------------------------------------------------------------

# 28. MCP Support

If MCP is available, represent MCP servers as capability providers.

``` text
MCP

filesystem:
available

github:
available

postgres:
available

browser:
unavailable
```

Reference only actually available MCP capabilities.

If an MCP server would materially improve a task, recommend it rather
than assuming it exists.

------------------------------------------------------------------------

# 29. Plugin Support

Plugins should be treated as one possible capability provider, not a
fundamental dependency.

``` text
CAPABILITY
    |
    +-- Native tool
    +-- MCP
    +-- Plugin
    +-- API
    +-- Local application
    +-- External service
```

The primary question is:

> **What capability is available?**

not:

> **Which integration technology provides it?**

------------------------------------------------------------------------

# 30. Runtime Capability Adapter

Implement a conceptual:

``` text
RuntimeCapabilityAdapter
```

Its purpose is to normalize different environments into the same
Capability Profile.

``` text
Claude Runtime
    |
Claude Adapter
    |
Capability Profile
```

``` text
Open WebUI
    |
Open WebUI Adapter
    |
Capability Profile
```

``` text
Custom Local Agent
    |
Local Runtime Adapter
    |
Capability Profile
```

The rest of Prompt Architect should operate on the normalized profile.

------------------------------------------------------------------------

# 31. Capability Sources

Each capability should record its source:

``` text
USER_DECLARED
RUNTIME_DETECTED
TOOL_DETECTED
MODEL_DOCUMENTATION
RUNTIME_DOCUMENTATION
CONFIGURATION
INFERRED
UNKNOWN
```

------------------------------------------------------------------------

# 32. Capability Conflict Resolution

Different sources may disagree.

Example:

``` text
User says:
Python is available.

Runtime inspection:
Python executable not found.
```

Use precedence:

``` text
Direct runtime evidence
        >
Explicit current configuration
        >
Official documentation
        >
Older user information
        >
Inference
```

When uncertainty remains, flag it.

------------------------------------------------------------------------

# 33. Capability Freshness

Capabilities can change.

Profiles should support:

``` text
timestamp
source
version
environment_id
confidence
```

Revalidate when:

-   The model changes.
-   The runtime changes.
-   Tools change.
-   Configuration changes.
-   A task depends on a previously uncertain capability.
-   The user explicitly requests verification.

------------------------------------------------------------------------

# 34. Reusable Capability Profiles

Profiles should be reusable.

Example:

``` text
PROFILE
├── Claude Code
├── Local Qwen
├── Open WebUI Qwen
├── Local Llama
└── Custom Agent
```

Users should not repeatedly answer the same capability questions.

------------------------------------------------------------------------

# 35. Capability Profile Updating

Profiles should be updateable.

Example:

``` text
Previous:
Python = unavailable

User added:
Python MCP server

Updated:
Python = available
```

Affected compatibility results should be invalidated and recompiled when
necessary.

------------------------------------------------------------------------

# 36. Prompt Compatibility Report

For complex Prompts, optionally provide:

``` text
TARGET
Local Qwen via Open WebUI

COMPATIBILITY
HIGH

AVAILABLE
✓ Filesystem
✓ Python
✓ Structured output

REQUIRED
✓ Filesystem
✓ Python

OPTIONAL
○ Web access

LIMITATIONS
✗ No browser

RESULT
Prompt can be executed as designed.
```

For simple tasks, omit this to avoid unnecessary output.

------------------------------------------------------------------------

# 37. Skill Compatibility Report

Skills receive equivalent analysis.

``` text
SKILL:
Repository Debugging Assistant

Target:
Local Qwen

Required:
✓ Filesystem
✓ Terminal
✓ Git

Missing:
✗ Terminal

Recommendation:
Add terminal execution capability.

Current compatibility:
PARTIAL
```

------------------------------------------------------------------------

# 38. Skill Generation

Capability analysis must work for:

``` text
PROMPT
SKILL
PROMPT + SKILL
SKILL UPDATE
SKILL EXTENSION
SKILL REFACTOR
```

A Skill should declare expected capabilities.

------------------------------------------------------------------------

# 39. Skill Portability

Skills should be portable where possible.

Prefer:

``` text
"If a filesystem capability is available, inspect the relevant files."
```

over:

``` text
"Use Claude's specific tool X."
```

Runtime-specific mappings should be separate.

------------------------------------------------------------------------

# 40. Capability-Aware Skill Compilation

A reusable Skill can be compiled against a specific runtime.

``` text
BASE SKILL
    |
CAPABILITY PROFILE
    |
ADAPTATION
    |
RUNTIME-SPECIFIC SKILL
```

Example:

``` text
Base:
"Use available database tools to inspect schema."

Claude:
"Use the connected database tool..."

Local:
"Use the configured PostgreSQL MCP..."

No database:
"Ask the user to provide the schema..."
```

------------------------------------------------------------------------

# 41. Capability Degradation

If a capability is missing, degrade gracefully where possible.

``` text
FULL MODE
Web + Browser + Filesystem + Python

DEGRADED MODE
Files + Python

MINIMAL MODE
User-provided documents + reasoning
```

Preserve the user's objective as much as possible.

------------------------------------------------------------------------

# 42. Hard Failure Conditions

Some gaps should stop execution-oriented compilation or explicitly mark
the output as non-executable.

Examples:

``` text
Required destructive action
+
No execution capability
```

or:

``` text
Required vision input
+
Text-only model
```

The Architect should never pretend these are executable.

------------------------------------------------------------------------

# 43. Capability-Aware Validation

Validate:

1.  Does the Prompt require unavailable tools?
2.  Does the Skill assume unsupported modalities?
3.  Does the workflow require unavailable execution?
4.  Does autonomy exceed runtime capabilities?
5.  Are permissions sufficient?
6.  Is context size practical?
7.  Are tool instructions mapped correctly?
8.  Are limitations honestly represented?
9.  Are fallback paths defined?
10. Are execution claims verifiable?

------------------------------------------------------------------------

# 44. Adversarial Capability Review

Test questions such as:

``` text
What happens if the browser is unavailable?

What happens if Python fails?

What happens if the model can read but not write?

What happens if the database is read-only?

What happens if the context is too large?

What happens if the model has vision but the runtime cannot provide images?

What happens if a tool is installed but disabled?
```

The Architect should identify hidden capability assumptions.

------------------------------------------------------------------------

# 45. Capability Misrepresentation Detection

Detect instructions such as:

``` text
"Search the web..."
"Run this code..."
"Edit the file..."
"Open the database..."
"Use the browser..."
"Inspect the repository..."
```

and compare them against the Capability Profile.

If unsupported:

``` text
CAPABILITY ERROR
```

The compiler should:

1.  Replace the instruction.
2.  Add a conditional instruction.
3.  Recommend a missing capability.
4.  Ask the user.
5.  Mark the task as not currently executable.

------------------------------------------------------------------------

# 46. Capability-Aware Output Modes

Support:

``` text
STRICT
```

Only generate instructions supported by confirmed capabilities.

``` text
ADAPTIVE
```

Generate capability-aware fallbacks.

``` text
RECOMMEND
```

Identify missing capabilities and recommend additions.

``` text
ABSTRACT
```

Generate portable Prompt/Skill instructions using abstract capabilities.

------------------------------------------------------------------------

# 47. Recommended Default

Use:

``` text
ADAPTIVE + RECOMMEND
```

for complex tasks.

This gives the user:

1.  A usable result now.
2.  Clear limitations.
3.  Recommended improvements.
4.  Optional tool additions.
5.  No false capability claims.

------------------------------------------------------------------------

# 48. User Experience Flow

The interaction should remain simple.

User:

> Make me a Skill that analyzes my local Excel files and creates charts.

Architect:

``` text
Target:
Local Qwen

Checking capabilities...
✓ File access
✓ Python
✓ Spreadsheet support

No critical gaps found.

Generating Skill...
```

If something is missing:

``` text
Target:
Local Qwen

Required:
✓ File access
✓ Python
✗ Excel writing

Your environment can analyze the files,
but cannot reliably modify/save Excel workbooks.

Recommended addition:
openpyxl or equivalent spreadsheet-writing capability.

I can still generate:
1. A fully executable Skill after adding it.
2. A degraded Skill that analyzes and generates modification code.
```

The user should not need to understand the underlying architecture.

------------------------------------------------------------------------

# 49. Dynamic Capability Questions

Do not use a fixed questionnaire.

Generate questions from:

``` text
TASK REQUIREMENTS
+
UNKNOWN CAPABILITIES
+
RISK
+
EXPECTED AUTONOMY
```

Examples:

Low-risk writing task:

``` text
No capability questions.
```

Repository modification:

``` text
Can the target access the repository?
Can it write files?
Can it run tests?
```

High-risk infrastructure task:

``` text
Can it execute commands?
What permissions does it have?
Can changes be rolled back?
```

------------------------------------------------------------------------

# 50. Minimal Discovery

The system must not turn every prompt request into a lengthy setup
process.

Use:

> **Discover automatically whenever possible. Ask only when the missing
> information materially changes the result.**

------------------------------------------------------------------------

# 51. Capability-Aware Compilation IR

Extend the existing Intermediate Representation with:

``` text
CAPABILITIES

TARGET
    model
    runtime
    version

AVAILABLE
    confirmed
    inferred

REQUIRED
    required
    recommended
    optional

GAPS
    blocking
    non_blocking

TOOLS
    available
    recommended
    missing

PERMISSIONS
    read
    write
    execute
    network
    database

LIMITATIONS
    model
    runtime
    context
    modality
    permissions

COMPATIBILITY
    status
    confidence
    fallbacks
```

------------------------------------------------------------------------

# 52. Extended Compilation Pipeline

The overall system becomes:

``` text
User Intent
    |
Understand
    |
Normalize
    |
Classify
    |
Determine Risk
    |
Determine Operating Mode
    |
Determine Autonomy
    |
Extract Requirements
    |
Identify Assumptions
    |
Identify Target Model
    |
Discover Capabilities
    |
Build Capability Profile
    |
Build Required Capability Profile
    |
Perform Capability Gap Analysis
    |
Recommend Tools / Integrations
    |
Resolve Critical Unknowns
    |
Collect Context
    |
Select Prompt / Skill Architecture
    |
Generate Workflow
    |
Compile Tool Rules
    |
Compose Prompt / Skill
    |
Capability Compatibility Review
    |
Adversarial Review
    |
Refine
    |
Validate
    |
Final Prompt / Skill
```

------------------------------------------------------------------------

# 53. Architectural Separation

Keep these concepts separate:

``` text
TASK ANALYSIS
What does the user want?

CAPABILITY ANALYSIS
What can the target do?

RESOURCE ANALYSIS
What information/resources are available?

TOOL ANALYSIS
What mechanisms provide capabilities?

AUTONOMY ANALYSIS
How independently should the target act?

RISK ANALYSIS
How dangerous is failure?

PROMPT/SKILL COMPILATION
How should all of this be expressed?
```

------------------------------------------------------------------------

# 54. Tool Recommendations Do Not Automatically Become Requirements

A recommended tool must not silently become mandatory.

Example:

``` text
Task:
Analyze PDFs.

Vision:
Not required.

OCR:
Recommended because scanned PDFs may exist.
```

Do not require OCR unless the task actually depends on scanned-image
text.

Use:

``` text
MUST
SHOULD
MAY
MUST_NOT
```

for capability recommendations as well.

------------------------------------------------------------------------

# 55. Capability Optimization

Consider whether adding a capability is actually worthwhile.

Example:

``` text
Task:
Summarize a text document.

Missing:
Web access

Decision:
Do not recommend web access.
Reason:
It provides no meaningful benefit for the requested task.
```

Another:

``` text
Task:
Research current GPU prices.

Missing:
Web access

Decision:
Recommend web access.
Reason:
Current external information is essential.
```

Avoid unnecessary tool bloat.

------------------------------------------------------------------------

# 56. Capability Cost Awareness

Where relevant, consider:

``` text
Complexity
Latency
Cost
Security
Privacy
Maintenance
Reliability
```

Prefer the least complex capability that reliably satisfies the
requirement.

A simple local task should not automatically require an external cloud
service.

------------------------------------------------------------------------

# 57. Security and Privacy

Capability recommendations must respect security boundaries.

Consider:

-   Network access.
-   Credential access.
-   Filesystem exposure.
-   Database exposure.
-   External data transfer.
-   Elevated permissions.
-   Third-party services.

For sensitive tasks, prefer local capabilities when they satisfy the
requirement.

------------------------------------------------------------------------

# 58. Tool Permission Mapping

Represent permissions explicitly:

``` text
TOOL:
filesystem

PERMISSIONS:
read = true
write = true
delete = false
execute = false
```

Generated instructions must stay within these permissions.

------------------------------------------------------------------------

# 59. Capability Profiles and Skills

A Skill should be able to declare:

``` text
CAPABILITY REQUIREMENTS
```

Example:

``` text
Required:
filesystem.read

Recommended:
python.execute

Optional:
web.search

Not required:
browser
```

When loaded into another environment, compatibility can be checked
automatically.

------------------------------------------------------------------------

# 60. Portable Skill Design

Prefer:

``` text
ABSTRACT CAPABILITY
```

over:

``` text
SPECIFIC TOOL NAME
```

unless the Skill is intentionally runtime-specific.

Example:

``` text
Abstract:
"Use an available source-control capability."

Runtime-specific:
"Use Git MCP."
```

------------------------------------------------------------------------

# 61. Runtime-Specific Compilation

When a user explicitly targets a runtime, compile a specialized version.

``` text
BASE SKILL
      |
Target = Claude Code
      |
Claude-specific tool mapping
      |
Claude Skill
```

or:

``` text
BASE SKILL
      |
Target = Local Qwen + Open WebUI
      |
Local tool mapping
      |
Open WebUI Skill
```

------------------------------------------------------------------------

# 62. Capability-Aware Research Tasks

If current information is required:

``` text
Required:
Web/search capability
```

If unavailable:

``` text
Do not pretend research was performed.
```

Instead:

``` text
Option A:
Recommend enabling web access.

Option B:
Ask the user to provide sources.

Option C:
Generate a research plan that can be executed later.
```

------------------------------------------------------------------------

# 63. Capability-Aware File Workflows

Distinguish:

``` text
READ FILE
WRITE FILE
CREATE FILE
MOVE FILE
DELETE FILE
EXECUTE FILE
```

A model with file-reading access does not automatically have all other
file capabilities.

------------------------------------------------------------------------

# 64. Capability-Aware Code Workflows

Distinguish:

``` text
READ CODE
GENERATE CODE
EDIT CODE
RUN CODE
RUN TESTS
DEBUG EXECUTION
BUILD PROJECT
DEPLOY PROJECT
```

Example:

``` text
Available:
✓ Read
✓ Generate
✓ Edit

Unavailable:
✗ Run
✗ Test

Generated behavior:
Make code changes, but do not claim tests were run.
Provide exact commands for the user/runtime to execute.
```

------------------------------------------------------------------------

# 65. Capability-Aware Database Workflows

Distinguish:

``` text
SCHEMA READ
DATA READ
DATA WRITE
DDL
TRANSACTION CONTROL
ADMINISTRATION
```

Example:

``` text
Schema:
READ

Data:
READ

Write:
NO

Generated Skill:
Can analyze and query data.
Must not attempt modifications.
```

------------------------------------------------------------------------

# 66. Capability-Aware Browser Workflows

Decompose browser capability where relevant:

``` text
SEARCH
NAVIGATE
READ
CLICK
TYPE
DOWNLOAD
UPLOAD
AUTHENTICATE
EXECUTE_WEB_ACTION
```

Browser availability does not automatically imply all actions are
permitted.

------------------------------------------------------------------------

# 67. Capability-Aware Verification

Every execution-oriented workflow should identify how results can be
verified.

``` text
Can execute:
YES

Can test:
YES

Can inspect output:
YES

Verification:
AUTOMATABLE
```

If verification is unavailable, lower confidence or introduce a human
checkpoint.

------------------------------------------------------------------------

# 68. Capability Confidence and Risk

Capability uncertainty should increase caution as task risk increases.

``` text
Low risk:
Unknown capability -> reasonable fallback

High risk:
Unknown capability -> verify before action

Critical risk:
Unknown capability -> do not authorize execution
```

------------------------------------------------------------------------

# 69. Capability-Aware Completion Criteria

Completion depends on what the runtime can verify.

If execution is unavailable:

``` text
Task is complete when the implementation is produced,
relevant checks are specified, and execution status is
explicitly reported.
```

If execution is available:

``` text
Task is complete when implementation is made and
relevant tests/checks pass.
```

------------------------------------------------------------------------

# 70. Capability-Aware Failure Handling

If a required tool is unavailable:

1.  Do not fabricate tool output.
2.  State the limitation.
3.  Determine whether a fallback exists.
4.  If safe, continue in degraded mode.
5.  If not, stop at the capability boundary.
6.  Explain what capability would unblock the task.

------------------------------------------------------------------------

# 71. Capability Change Detection

If runtime capabilities change during a task:

``` text
Python initially unavailable.

Later:
Python tool becomes available.

Action:
Re-evaluate affected workflow steps.
```

Do not continue operating under stale assumptions.

------------------------------------------------------------------------

# 72. Capability Profiles and Testing

Test generated artifacts against multiple runtime profiles.

Example:

``` text
TEST PROFILE A
Full tools

TEST PROFILE B
Filesystem only

TEST PROFILE C
No execution

TEST PROFILE D
Read-only database

TEST PROFILE E
No web
```

------------------------------------------------------------------------

# 73. Compatibility Matrix

Support a matrix such as:

  Capability              Required   Available Result
  ------------------ ------------- ----------- --------
  Filesystem read              Yes         Yes Pass
  Filesystem write             Yes          No Fail
  Python execution             Yes         Yes Pass
  Web                           No          No Pass
  Vision               Recommended         Yes Pass

------------------------------------------------------------------------

# 74. Example --- Local Model

User:

> Create a Skill that manages my project files, runs tests, and fixes
> errors.

Capability profile:

``` text
Model:
Local Qwen

Filesystem:
READ ✓
WRITE ✓

Terminal:
✗

Python:
✓

Git:
✗
```

Required:

``` text
Filesystem:
Required ✓

Terminal:
Required ✗

Test execution:
Required ✗

Git:
Optional
```

Result:

``` text
COMPATIBILITY:
PARTIAL

Blocking gap:
Terminal execution

Recommendation:
Add terminal/shell capability.

Fallback:
Generate commands and analyze user-provided test output.
```

------------------------------------------------------------------------

# 75. Example --- Claude With Tools

User:

> Create a Skill that researches documentation, edits my repository,
> runs tests, and prepares a summary.

Capability profile:

``` text
Web:
✓

Repository:
✓

Filesystem:
✓

Terminal:
✓

Git:
✓
```

Result:

``` text
COMPATIBILITY:
FULL

Operating mode:
ORCHESTRATOR + ENGINEER

Autonomy:
A3/A4 depending on risk

Skill:
Fully executable workflow
```

------------------------------------------------------------------------

# 76. Example --- Text-Only Model

User:

> Create a Skill that analyzes images from a local folder.

Capability profile:

``` text
Text:
✓

Filesystem:
✓

Vision:
✗
```

Result:

``` text
BLOCKING GAP:
Vision

Possible solutions:
1. Use a vision-capable model.
2. Add an image-analysis service.
3. Preprocess images into machine-readable descriptions.
```

------------------------------------------------------------------------

# 77. Example --- Research Without Web

User:

> Create a Skill that finds the latest information about NVIDIA GPUs.

Capability:

``` text
Web:
✗
```

Result:

``` text
Required:
Web/search

Status:
Unavailable

Recommendation:
Enable web access.

Fallback:
Provide URLs/documents manually.
```

------------------------------------------------------------------------

# 78. Example --- File Editing Without Write Access

User:

> Create a Skill that edits my Word documents.

Capability:

``` text
Read:
✓

Write:
✗
```

Result:

``` text
Analysis:
Possible

Modification:
Not currently possible

Fallback:
Generate exact changes or a transformation script.
```

------------------------------------------------------------------------

# 79. Capability-Aware Tool Recommendation UX

Keep recommendations concise.

``` text
CAPABILITY GAP

Your task requires:
Python execution

Currently available:
✗

Recommended:
Add Python execution

Alternative:
I can generate the Python script for manual execution.
```

------------------------------------------------------------------------

# 80. Integration With Existing Plan

This extension integrates with the existing Prompt Architect stages
rather than creating a parallel architecture.

Add conceptual stages:

``` text
Stage X — Target Identification
Stage X+1 — Capability Discovery
Stage X+2 — Required Capability Analysis
Stage X+3 — Capability Gap Analysis
Stage X+4 — Tool Recommendation
Stage X+5 — Compatibility Validation
```

The exact numbering should be reconciled with the final main plan during
implementation.

------------------------------------------------------------------------

# 81. Updated Core Design

Prompt Architect should now be understood as:

``` text
PROMPT ARCHITECT

INPUT
Natural-language intent

ANALYSIS
Task
Risk
Requirements
Context
Target
Capabilities
Resources
Permissions

COMPILATION
Prompt / Skill architecture
Workflow
Tool rules
Validation
Fallbacks

QUALITY CONTROL
Prompt quality
Capability compatibility
Security
Risk
Evidence
Regression resistance

OUTPUT
Prompt
Skill
Prompt + Skill
Skill Update
Skill Extension
Skill Refactor
```

------------------------------------------------------------------------

# 82. New Final Design Principles

Add:

> **A high-quality Prompt is not merely well-written; it is executable
> within the capabilities, permissions, resources, and constraints of
> its target environment.**

And:

> **When required capabilities are missing, Prompt Architect should
> identify the gap, recommend a viable capability addition when
> possible, and otherwise produce the safest useful degraded workflow
> rather than pretending the capability exists.**

------------------------------------------------------------------------

# 83. Implementation Priority

Implement incrementally.

## Phase 1 --- Capability Schema

Implement:

``` text
CapabilityProfile
RequiredCapabilityProfile
CapabilityGap
CompatibilityResult
```

## Phase 2 --- Manual Target Profiles

Support profiles such as:

``` text
Claude
Local Qwen
Open WebUI
Custom Agent
```

## Phase 3 --- Model Research

Add model documentation research.

## Phase 4 --- Runtime Inspection

Detect actual tools and permissions when possible.

## Phase 5 --- Gap Analysis

Automatically compare required vs available capabilities.

## Phase 6 --- Tool Recommendations

Recommend missing tools/integrations.

## Phase 7 --- Capability-Aware Compilation

Generate runtime-specific Prompts and Skills.

## Phase 8 --- Compatibility Testing

Test generated artifacts against multiple capability profiles.

------------------------------------------------------------------------

# 84. Non-Goals

This extension should not turn Prompt Architect into:

-   A generic package manager.
-   An unrestricted system administrator.
-   An automatic tool installer.
-   A universal agent runtime.
-   A replacement for MCP.
-   A replacement for model documentation.
-   A system that installs tools without user authorization.

Its responsibility is:

> **Understand capabilities, reason about requirements, identify gaps,
> recommend solutions, and compile compatible instructions.**

------------------------------------------------------------------------

# 85. Final Architecture

``` text
                         PROMPT ARCHITECT
                                |
             +------------------+------------------+
             |                  |                  |
             v                  v                  v
        TASK ANALYSIS      TARGET ANALYSIS    CONTEXT ANALYSIS
             |                  |                  |
             |                  v                  |
             |          CAPABILITY DISCOVERY      |
             |                  |                  |
             |          +-------+-------+          |
             |          v               v          |
             |       MODEL           RUNTIME       |
             |          |               |          |
             |          +-------+-------+          |
             |                  v                  |
             |          CAPABILITY PROFILE        |
             |                  |                  |
             +-------------+----+------------------+
                           v
                REQUIRED CAPABILITIES
                           |
                           v
                    CAPABILITY GAP
                       ANALYSIS
                           |
                +----------+----------+
                v                     v
          COMPATIBLE              GAPS FOUND
                |                     |
                |              TOOL RECOMMENDATION
                |                     |
                +----------+----------+
                           v
                  PROMPT / SKILL IR
                           |
                           v
                    TOOL RULES
                    WORKFLOW
                    FALLBACKS
                    VALIDATION
                           |
                           v
                  CAPABILITY REVIEW
                           |
                           v
                 ADVERSARIAL REVIEW
                           |
                           v
                       COMPILE
                           |
                           v
                  FINAL PROMPT / SKILL
```

------------------------------------------------------------------------

# 86. End Goal

The ultimate behavior should feel like this:

\`\`\`text USER: "I want a Skill that does X."

PROMPT ARCHITECT:

1.  Understands X.
2.  Determines what X requires.
3.  Identifies the target model/runtime.
4.  Determines what that environment can actually do.
5.  Researches unknown model/runtime capabilities when appropriate.
6.  Asks only important unanswered questions.
7.  Detects missing capabilities.
8.  Recommends tools/integrations when they can be added.
9.  Determines whether the task can be fully, partially, or not
    executed.
10. Compiles the Prompt or Skill around the actual environment.
11. Adds fallbacks where appropriate.
12. Validates that no unsupported capability is assumed.
13. Produces the final artifact.

The result is not simply:

"Here is a good prompt."

It is:

"Here is the best Prompt/Skill for what you want, specifically compiled
for what your target model and environment can actually do."
