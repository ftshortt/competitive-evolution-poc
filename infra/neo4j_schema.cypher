// Neo4j Graph Schema and Example Queries for Competitive Evolution POC
// ---------------------------------------------------------------
// This file initializes constraints, provides example data creation patterns,
// defines relationship patterns, and includes analytical queries to study
// evolutionary progress, hybridization, and model-task routing.

// 1) CONSTRAINTS: Ensure uniqueness on key identifiers
// ----------------------------------------------------
// Using IF NOT EXISTS syntax so the script is idempotent.
CREATE CONSTRAINT IF NOT EXISTS FOR (s:Solution) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (t:Task)     REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (m:Model)    REQUIRE m.name IS UNIQUE;

// 2) EXAMPLE NODE CREATION PATTERNS
// ----------------------------------
// These are examples; adapt values as needed. MERGE ensures no duplicates.

// Example Solution node
MERGE (s:Solution {
  id: "sol_0001",
  pool: "main",
  pool_trait: "reasoning-depth",
  generation: 12,
  fitness: 0.86,
  code: "# pseudocode for solution ...",
  reasoning_trace: "Chain-of-thought summary or distilled rationale",
  reasoning_steps: 7,
  token_cost: 12450,
  task_type: "code_synthesis",
  timestamp: datetime()
});

// Example Task node
MERGE (t:Task {
  id: "task_qa_001",
  domain: "qa",
  objective: "Answer domain-specific questions with sources",
  complexity: "medium"
});

// Example Model node
MERGE (m:Model {
  name: "gpt-4o-mini",
  pool: "main",
  specialization: "generalist"
});

// 3) RELATIONSHIP CREATION PATTERNS
// ---------------------------------
// EVOLVED_FROM: connects a descendant Solution to its parent Solution
// Properties: mutation_type, fitness_delta, generation_gap
MATCH (child:Solution {id: "sol_0001"})
MERGE (parent:Solution {id: "sol_0000"})
MERGE (child)-[:EVOLVED_FROM {
  mutation_type: "prompt_mutation",
  fitness_delta: 0.10,
  generation_gap: 1
}]->(parent);

// HYBRID_OF: child Solution synthesized from multiple parents
// Properties: weights (map or list), synthesis_method
MATCH (hyb:Solution {id: "sol_0002"})
MERGE (p1:Solution {id: "sol_0001"})
MERGE (p2:Solution {id: "sol_0000"})
MERGE (hyb)-[:HYBRID_OF {
  weights: [0.6, 0.4],
  synthesis_method: "crossover_weighted_merge"
}]->(p1)
MERGE (hyb)-[:HYBRID_OF {
  weights: [0.6, 0.4],
  synthesis_method: "crossover_weighted_merge"
}]->(p2);

// GENERATED_BY: Solution produced by a particular Model
MATCH (s1:Solution {id: "sol_0001"}), (m1:Model {name: "gpt-4o-mini"})
MERGE (s1)-[:GENERATED_BY]->(m1);

// SOLVES: Solution solves a Task (with optional performance properties)
MATCH (s1:Solution {id: "sol_0001"}), (t1:Task {id: "task_qa_001"})
MERGE (s1)-[:SOLVES {score: 0.86, latency_ms: 1200}]->(t1);

// OUTPERFORMS: Solution A outperforms Solution B on a domain or metric
// Properties: margin (absolute or relative), domain
MATCH (a:Solution {id: "sol_0001"}), (b:Solution {id: "sol_0000"})
MERGE (a)-[:OUTPERFORMS {margin: 0.10, domain: "qa"}]->(b);

// 4) ANALYTICAL QUERIES
// ----------------------
// a) Best evolutionary lineage query: follow EVOLVED_FROM back to the earliest
// ancestor and compute cumulative improvements along the path.
// Returns lineage nodes, edges, and aggregate metrics.
MATCH path = (leaf:Solution)-[:EVOLVED_FROM*]->(root:Solution)
WHERE leaf.fitness IS NOT NULL AND NOT (leaf)-[:EVOLVED_FROM]->()
WITH path, leaf, root,
     reduce(delta = 0.0, r IN relationships(path) | delta + coalesce(r.fitness_delta, 0.0)) AS total_delta,
     length(path) AS hops
RETURN leaf.id AS leaf_id, root.id AS root_id, hops, total_delta, path
ORDER BY leaf.fitness DESC, total_delta DESC
LIMIT 5;

// b) Trait specialization analysis: which pools/traits correlate with higher fitness
MATCH (s:Solution)
WITH s.pool AS pool, s.pool_trait AS trait, avg(coalesce(s.fitness,0)) AS avg_fitness,
     count(*) AS n
RETURN pool, trait, n, avg_fitness
ORDER BY avg_fitness DESC, n DESC
LIMIT 20;

// c) Hybrid advantage detection: compare hybrids to their parent average
MATCH (h:Solution)-[r:HYBRID_OF]->(p:Solution)
WITH h, collect(p.fitness) AS parent_fitnesses, count(*) AS k
WHERE k >= 2 AND h.fitness IS NOT NULL
WITH h, parent_fitnesses, reduce(avgp = 0.0, f IN parent_fitnesses | avgp + coalesce(f,0.0)) / size(parent_fitnesses) AS parent_avg
RETURN h.id AS hybrid_id, h.fitness AS hybrid_fitness, parent_avg, (h.fitness - parent_avg) AS advantage
ORDER BY advantage DESC
LIMIT 10;

// d) Model efficiency comparison: fitness per token or per latency
MATCH (s:Solution)-[:GENERATED_BY]->(m:Model)
WITH m.name AS model, avg(s.fitness) AS avg_fitness, avg(s.token_cost) AS avg_tokens
RETURN model, avg_fitness, avg_tokens, (avg_fitness / CASE WHEN avg_tokens = 0 THEN 1 ELSE avg_tokens END) AS fitness_per_token
ORDER BY fitness_per_token DESC
LIMIT 10;

// e) Task-specific model routing: pick top model for a given task domain
// Example: domain = "qa"; adjust WHERE clause as needed
MATCH (s:Solution)-[:GENERATED_BY]->(m:Model)
MATCH (s)-[:SOLVES]->(t:Task)
WHERE t.domain = "qa"
WITH m.name AS model, avg(s.fitness) AS avg_fitness, count(*) AS n
WHERE n >= 3
RETURN model, n, avg_fitness
ORDER BY avg_fitness DESC
LIMIT 5;
