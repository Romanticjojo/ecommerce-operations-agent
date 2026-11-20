# Architecture and UML

Commerce Lens uses one controller. In full model mode a provider returns a bounded plan and the application compiles it into SQL. The direct baseline asks the provider for candidate SQL. Both use the same reporting views and execution limits. The first three diagrams address the UML portion of the course rubric. The entity-relationship diagram documents the data model.

## 1. UML class diagram of analytical contracts

```mermaid
classDiagram
    class AgentController {
        +ask(QueryRequest) AnswerEnvelope
    }
    class ModelAdapter {
        +plan(question, catalog) QueryPlan
        +direct(question, catalog) SQLDraft
    }
    class Catalog {
        +schema() SchemaContext
        +metrics() MetricDefinition[]
    }
    class SafeExecutor {
        +validate(sql) ValidationResult
        +execute(sql) QueryResult
    }
    class ReviewAnalyzer {
        +investigate(filters) StatisticalResult
    }
    class EvidenceComposer {
        +compose(plan, result) AnswerEnvelope
    }
    class RunStore {
        +save(run) request_id
        +get(request_id) Run
    }
    class EvaluationRunner {
        +run(dataset, mode) EvaluationReport
    }
    AgentController --> ModelAdapter
    AgentController --> Catalog
    AgentController --> SafeExecutor
    AgentController --> ReviewAnalyzer
    AgentController --> EvidenceComposer
    AgentController --> RunStore
    EvaluationRunner --> AgentController
```

Each box describes a logical interface implemented by Python modules. The class view shows which interfaces can be tested independently. Candidate sales SQL passes through the guard. The review analyzer owns fixed, read-only statistical queries and records them in its evidence.

## 2. UML sequence diagram of a sales request

```mermaid
sequenceDiagram
    actor User as Operator
    participant Web as Workbench
    participant API as Agent API
    participant Model as Model adapter
    participant Guard as Guard and worker
    participant DB as Read-only DuckDB
    participant Store as Run history
    User->>Web: Ask a question
    Web->>API: QueryRequest
    API->>Model: Question, schema and metric definitions
    Model-->>API: QueryPlan
    API->>API: Compile SQL from the metric definition
    API->>Guard: Validate and execute candidate SQL
    alt Approved query
        Guard->>DB: Bounded read-only query
        DB-->>Guard: Columns, rows and truncation flag
        Guard-->>API: QueryResult
        API->>Store: Save SQL, filters, evidence and timing
        API-->>Web: AnswerEnvelope
        Web-->>User: Answer, chart, table and SQL
    else Rejected query
        Guard-->>API: Rejection reason
        API->>Store: Save outcome
        API-->>Web: Rejected result
        Web-->>User: Reason and next step
    end
```

The sequence view shows when a proposed plan becomes an executed query, which component reads the snapshot and when evidence is saved. Clarification can finish upstream during planning. The offline demo uses a local parser at the planning step.

## 3. UML state diagram of a request

```mermaid
stateDiagram-v2
    [*] --> Received
    Received --> Planning
    Planning --> Clarification: Ambiguous question
    Planning --> Rejected: Outside scope
    Planning --> Repairing: Invalid structured plan
    Repairing --> Planning: One repair attempt
    Planning --> Failed: Provider or final schema error
    Planning --> Drafting: Valid sales plan
    Drafting --> Validating
    Validating --> Rejected: Disallowed operation
    Validating --> Failed: Invalid SQL
    Validating --> Executing: Approved
    Executing --> Failed: Timeout or database error
    Executing --> InsufficientData: No eligible rows
    Executing --> Checking: Rows returned
    Checking --> Completed: Format result and evidence
    Completed --> [*]
    Rejected --> [*]
    Clarification --> [*]
    InsufficientData --> [*]
    Failed --> [*]
```

The state view identifies terminal outcomes a user can encounter and the single permitted schema repair. It helps reviewers check that a timeout or empty sample reaches the right UI state. Statistical investigations take their own fixed-query path.

## 4. Entity-relationship diagram

```mermaid
erDiagram
    customers ||--o{ orders : places
    orders ||--o{ order_items : contains
    orders ||--o{ order_payments : paid_by
    orders ||--o{ order_reviews : reviewed_by
    products ||--o{ order_items : listed_in
    sellers ||--o{ order_items : fulfills
    orders ||--|| order_summary : summarized_as
    orders ||--o| order_review_delivery : sampled_as
```

The relationships describe the intended grains. Import audits test the actual keys, cardinalities and missing links. Aggregating items and payments independently avoids multiplying revenue. Choosing one eligible review per order supplies the unit of analysis for inference. Olist v2 also supplies the imported category translation and audit-only geolocation file. [Data dictionary](data-dictionary.md)

## Deployment

FastAPI serves the built React workbench and its API from one origin. Analytical requests read a DuckDB snapshot and write history to a separate local SQLite database. When configured, the model adapter calls the operator's chosen endpoint. Local CLI commands handle imports and batch evaluation. Native and Docker startup bind to the loopback interface by default.


## Named analysis procedures

The workbench reads skill descriptions and steps from `GET /api/skills` and submits the selected procedure ID and canonical question to `POST /api/query`. The controller checks the ID, date bounds and question before running the packaged read-only query locally. In model mode the full planner can also choose an allowlisted procedure and include supported dates. The direct SQL baseline retains its original reporting-view restrictions. Each procedure returns its executed query, table, conclusion, scope and interpretation notes in the existing history envelope. The model receives no stored review text or warehouse rows.
