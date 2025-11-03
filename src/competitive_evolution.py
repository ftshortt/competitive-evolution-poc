...            shinka_fitness.labels(model=name, generation=str(gen), domain=domain).set(fitness)
            fitness_scores.append((name, fitness, domain))
        # Selection per domain: top 2
        fitness_scores.sort(key=lambda x: (x[2], x[1]), reverse=True)
        by_domain: Dict[str, List[Tuple[str, float]]] = {}
        for n, f, d in fitness_scores:
            by_domain.setdefault(d, []).append((n, f))

        new_population: List[Tuple[str, AgentWeightMixin, str]] = population[:]
        for d, lst in by_domain.items():
            lst.sort(key=lambda x: x[1], reverse=True)
            if len(lst) >= 2:
                a_name, _ = lst[0]
                b_name, _ = lst[1]
                # map to instances
                by_name = {n: a for n, a, dom in population if dom == d}
                a_agent = by_name[a_name]
                b_agent = by_name[b_name]
                child = produce_offspring(a_agent, b_agent, name=f"child_{gen}_{d}_{a_name}_{b_name}", alpha=0.6, mutation_rate=0.12)
                # instantiate same class as parent A if possible
                if isinstance(a_agent, EvolvableDeepSeekOCR):
                    child_agent = EvolvableDeepSeekOCR(api_key=DEEPSEEK_OCR_API_KEY)
                elif isinstance(a_agent, DFIRHeuristicAgent):
                    child_agent = DFIRHeuristicAgent()
                elif isinstance(a_agent, SimpleCoderAgent):
                    child_agent = SimpleCoderAgent()
                else:
                    continue
                child_agent.set_weights(child.weights)
                new_population.append((child.name, child_agent, d))
        population = new_population

    print("Evolution complete.")

if __name__ == "__main__":
    main()
