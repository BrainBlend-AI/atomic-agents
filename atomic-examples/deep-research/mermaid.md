```mermaid
flowchart TD
    %% Pipeline overview — first turn
    Start([User question]) --> P[PlannerAgent]
    P -->|sub-topics + initial queries| Loop

    subgraph Loop["Per sub-topic — bounded by max_depth_per_sub_topic"]
        S[SearXNG search] --> Sc[Webpage scraper]
        Sc --> E[ExtractorAgent]
        E -->|claims tagged with source_id| R{ReflectorAgent}
        R -->|sufficient = true| Done
        R -->|next_queries| S
    end

    Done --> W1[WriterAgent — draft]
    W1 --> W2[WriterAgent — verify]
    W2 --> Out([Cited markdown report])

    classDef agent fill:#4CAF50,stroke:#2E7D32,color:#fff;
    classDef tool fill:#FF9800,stroke:#EF6C00,color:#fff;
    classDef terminator fill:#9C27B0,stroke:#6A1B9A,color:#fff;

    class P,E,W1,W2 agent;
    class R agent;
    class S,Sc tool;
    class Start,Out,Done terminator;
```

```mermaid
flowchart TD
    %% Chat-mode routing — every turn after the first
    U([Follow-up message]) --> D{DeciderAgent}
    D -->|needs_research = true| Plan[PlannerAgent — extend coverage]
    Plan --> Research[Search → Scrape → Extract → Reflect]
    Research --> QA[QAAgent]
    D -->|needs_research = false| QA
    QA --> Reply([Cited answer + follow-ups])

    classDef agent fill:#4CAF50,stroke:#2E7D32,color:#fff;
    classDef terminator fill:#9C27B0,stroke:#6A1B9A,color:#fff;

    class D,Plan,QA agent;
    class Research agent;
    class U,Reply terminator;
```

