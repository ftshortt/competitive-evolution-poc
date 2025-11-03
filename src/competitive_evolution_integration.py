pe"""Competitive evolution integration: wire realistic tasks and fitness for R1 and Qwen.
Replaces random fitness with domain scoring: DFIR, OCR, and coding benchmarks.
"""
from typing import List, Dict, Any, Tuple
import random
from copy import deepcopy

from src.utils import Task
from src.production_fitness import ProductionFitnessEvaluator
from src.deepseek_r1 import EvolvableDeepSeekR1  # assume wrapper exposes get/set/update
from src.qwen_coder import EvolvableQwenCoder   # assume wrapper exposes get/set/update
from src.deepseek_ocr import DeepSeekOCRAgent

# Domain task types (mirroring competitive_evolution definitions)
class DFIRLogTask(Task):
    def __init__(self, log_lines: List[str], ioc_patterns: List[str], expected_findings: Dict[str, int], generation: int = 0):
        self.log_lines = log_lines
        self.ioc_patterns = ioc_patterns
        self.expected_findings = expected_findings
        self.generation = generation

class OCRDocTask(Task):
    def __init__(self, image_bytes: bytes, expected_fields: Dict[str, str], generation: int = 0):
        self.image_bytes = image_bytes
        self.expected_fields = expected_fields
        self.generation = generation

class CodingBenchmarkTask(Task):
    def __init__(self, prompt: str, tests: List[Tuple[str, Any]], expected_score: float, generation: int = 0):
        self.prompt = prompt
        self.tests = tests
        self.expected_score = expected_score
        self.generation = generation

class DomainFitness(ProductionFitnessEvaluator):
    def eval_dfir(self, task: DFIRLogTask, findings: Dict[str, int]) -> float:
        tp = sum(min(findings.get(ioc, 0), cnt) for ioc, cnt in task.expected_findings.items())
        fp = sum(max(findings.get(ioc, 0) - task.expected_findings.get(ioc, 0), 0) for ioc in findings.keys())
        fn = sum(max(task.expected_findings.get(ioc, 0) - findings.get(ioc, 0), 0) for ioc in task.expected_findings.keys())
        precision = tp / (tp + fp + 1e-6)
        recall = tp / (tp + fn + 1e-6)
        return 2*precision*recall/(precision+recall+1e-6)

    def eval_ocr(self, task: OCRDocTask, extracted: Dict[str, str]) -> float:
        import difflib
        scores = []
        for k, expected in task.expected_fields.items():
            got = (extracted or {}).get(k, "")
            ratio = difflib.SequenceMatcher(None, expected.strip().lower(), str(got).strip().lower()).ratio()
            scores.append(ratio)
        return sum(scores)/max(1, len(scores))

    def eval_coding(self, task: CodingBenchmarkTask, results: List[Tuple[str, bool]]) -> float:
        passed = sum(1 for _, ok in results if ok)
        return passed / max(1, len(results))

# Minimal executors for R1 and Qwen (placeholder hooks)
class R1Reasoner(EvolvableDeepSeekR1):
    def solve_dfir(self, task: DFIRLogTask) -> Dict[str, int]:
        # Placeholder heuristic until API wired: count ioc occurrences
        import re
        findings: Dict[str, int] = {}
        for pat in task.ioc_patterns:
            rx = re.compile(pat)
            total = sum(1 for line in task.log_lines if rx.search(line))
            if total:
                findings[pat] = total
        return findings

class QwenCoderBench(EvolvableQwenCoder):
    def solve_coding(self, task: CodingBenchmarkTask) -> List[Tuple[str, bool]]:
        # Placeholder: run provided tests to simulate pass rate
        out: List[Tuple[str, bool]] = []
        for name, checker in task.tests:
            try:
                ok = bool(checker()) if callable(checker) else bool(checker)
            except Exception:
                ok = False
            out.append((name, ok))
        return out

# Population and evolution
def create_population(api_key: str, per_type: int = 4) -> Dict[str, List]:
    pop = {'r1': [], 'qwen': []}
    for _ in range(per_type):
        pop['r1'].append(R1Reasoner(api_key=api_key))
        pop['qwen'].append(QwenCoderBench(api_key=api_key))
    return pop

def evaluate(pop: Dict[str, List], tasks: Dict[str, List[Task]]) -> Dict[str, List[float]]:
    fit = DomainFitness()
    scores = {'r1': [], 'qwen': []}
    for a in pop['r1']:
        s = 0.0
        cnt = 0
        for t in tasks.get('dfir', []):
            findings = a.solve_dfir(t)
            s += fit.eval_dfir(t, findings)
            cnt += 1
        scores['r1'].append(s/max(1, cnt))
    for a in pop['qwen']:
        s = 0.0
        cnt = 0
        for t in tasks.get('coding', []):
            results = a.solve_coding(t)
            s += fit.eval_coding(t, results)
            cnt += 1
        scores['qwen'].append(s/max(1, cnt))
    return scores

def select_and_reproduce(pop: Dict[str, List], scores: Dict[str, List[float]], mutation_rate: float = 0.1) -> Dict[str, List]:
    new_pop = {'r1': [], 'qwen': []}
    # R1
    order = sorted(range(len(pop['r1'])), key=lambda i: scores['r1'][i], reverse=True)
    elites = order[:max(1, len(order)//4)]
    for idx in elites:
        new_pop['r1'].append(pop['r1'][idx])
    while len(new_pop['r1']) < len(pop['r1']):
        a, b = random.sample(elites, k=min(2, len(elites)))
        pa, pb = pop['r1'][a], pop['r1'][b]
        child = R1Reasoner(api_key=pa.api_key)
        child.set_weights(pa.get_weights())
        if random.random() < 0.5:
            merged = deepcopy(pa.get_weights())
            for k, v in pb.get_weights().items():
                if isinstance(v, (int, float)):
                    merged[k] = 0.6*v + 0.4*merged.get(k, v)
            child.set_weights(merged)
        if random.random() < mutation_rate:
            child = child.mutate(mutation_rate=mutation_rate)
        new_pop['r1'].append(child)
    # Qwen
    order = sorted(range(len(pop['qwen'])), key=lambda i: scores['qwen'][i], reverse=True)
    elites = order[:max(1, len(order)//4)]
    for idx in elites:
        new_pop['qwen'].append(pop['qwen'][idx])
    while len(new_pop['qwen']) < len(pop['qwen']):
        a, b = random.sample(elites, k=min(2, len(elites)))
        pa, pb = pop['qwen'][a], pop['qwen'][b]
        child = QwenCoderBench(api_key=pa.api_key)
        child.set_weights(pa.get_weights())
        if random.random() < 0.5:
            child = pa.crossover(pb)
        if random.random() < mutation_rate:
            child = child.mutate(mutation_rate=mutation_rate)
        new_pop['qwen'].append(child)
    return new_pop

def run_competitive_evolution(api_key: str, generations: int = 5, per_type: int = 4) -> Dict[str, Any]:
    # Build tiny demo tasks
    tasks: Dict[str, List[Task]] = {
        'dfir': [
            DFIRLogTask(
                log_lines=[
                    "conn from 10.0.0.5 to evil.com",
                    "process rundll32.exe /i:random",
                    "dns query for evil.com",
                ],
                ioc_patterns=[r"evil\.com", r"rundll32\.exe"],
                expected_findings={r"evil\.com": 2, r"rundll32\.exe": 1},
            )
        ],
        'coding': [
            CodingBenchmarkTask(
                prompt="Implement add(a,b)",
                tests=[("add_small", lambda: 1+1==2), ("add_neg", lambda: -3+2==-1)],
                expected_score=1.0,
            )
        ],
    }
    pop = create_population(api_key, per_type)
    for g in range(generations):
        sc = evaluate(pop, tasks)
        pop = select_and_reproduce(pop, sc, mutation_rate=0.12)
    return {'population': pop, 'last_scores': sc}

if __name__ == "__main__":
    import os
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    res = run_competitive_evolution(api_key=api_key)
    print("Done", {k: len(v) for k,v in res['population'].items()})
