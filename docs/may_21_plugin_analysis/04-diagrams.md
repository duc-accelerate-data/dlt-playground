# Side-by-Side Flow Diagrams

## Older version (5.8.0) — driven by an auto-start helper, organised into six phases

```mermaid
flowchart TD
    Hook([Auto-start helper at session start])
    Hook -->|paste classification instructions + domain config| P0

    P0[Phase 0: Intake<br/>classify the user's request<br/>identify scope]
    P1[Phase 1: Workspace<br/>set up DuckDB or Fabric workspace]
    P2[Phase 2: Requirements<br/>write intent.md → requirements reviewer]
    P3[Phase 3: Design<br/>write design.md → design reviewer]
    P4{Phase 4: Build}
    P4a[Ingestion track<br/>discover schema → profile<br/>→ generate pipeline → run<br/>→ pin schema → run tests]
    P4b[Transformation track<br/>apply medallion → generate dbt<br/>→ run → run unit tests]
    P4c[Reviewers<br/>unit-test, data-test, code reviewers]
    P5[Phase 5: Publish<br/>document everything → publish contracts<br/>→ evaluate]

    P0 --> P1 --> P2 --> P3 --> P4
    P4 --> P4a --> P4c
    P4 --> P4b --> P4c
    P4c --> P5
```

## Newer version (0.1.3) — driven by the step-by-step plan

```mermaid
flowchart TD
    Start([Coordinator starts up])
    Start --> Resume{Is there an<br/>existing plan file?}
    Resume -->|yes| Loop
    Resume -->|no| Classify

    Classify[Classify the user's request<br/>drop the task-ran marker file]
    Design[Write intent.md → write design.md<br/>with Model/Pipeline Inventory + Gate Status]
    Plan[Emit the step-by-step plan<br/>each step names a task to run]

    Loop[Loop: read next step where status is not done<br/>load the task it names → run it<br/>mark step done]

    Classify --> Design --> Plan --> Loop

    Loop --> Track{What kind of step?}
    Track -->|ingestion| ING[set up → discover schema<br/>→ generate pipeline → run → pin<br/>→ run ingestion tests<br/>→ document → evaluate]
    Track -->|transformation| TR[set up → apply medallion<br/>→ generate dbt → run → run tests<br/>→ document → publish contracts<br/>→ evaluate]
    ING --> Gate
    TR --> Gate
    Gate[Reviewers run at each gate<br/>structured verdict pasted verbatim<br/>checkmarks added to design.md Gate Status]
    Gate --> Loop
```

## What moved where

```mermaid
flowchart LR
    subgraph Old["Older plugin (5.8.0)"]
        Oh[Auto-start helper script]
        Ol[Supporting library:<br/>contracts + error codes<br/>+ readiness + templates]
        Os[Helper scripts:<br/>Fabric helpers + validators]
        Osh[Shared references (flat layout)]
    end

    subgraph New["Newer plugin (0.1.3-med)"]
        Nsh[Shared folder:<br/>conventions, playbooks,<br/>patterns tagged variant: med,<br/>templates including the plan template]
        Nc[Coordinator's prompt<br/>absorbed classification trigger<br/>and plan/resume logic]
        Ne[Pushed outside the plugin:<br/>repo-level CI,<br/>Studio host validation]
    end

    Oh -. removed .-> Nc
    Ol -. mostly removed .-> Nsh
    Ol -. some validation .-> Ne
    Os -. removed .-> Ne
    Osh -. reorganised .-> Nsh
```
