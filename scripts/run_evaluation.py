import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import run_agent


def load_questions(json_path: str) -> list:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_answer(answer: str, ground_truth: str) -> bool:
    """
    Simple keyword-based check for evaluation.
    """
    answer_lower = answer.lower()
    truth_lower = ground_truth.lower()

    if truth_lower in answer_lower:
        return True

    # Handle yes/no questions
    if truth_lower == "yes" and ("detected" in answer_lower or "found" in answer_lower):
        return True
    if truth_lower == "no" and ("not" in answer_lower or "unable" in answer_lower):
        return True

    return False


def main():
    image_dir = Path("data/evaluation/images")
    questions_path = Path("data/evaluation/questions.json")

    if not image_dir.exists():
        print("Error: Image directory not found.")
        return

    if not questions_path.exists():
        print("Error: Questions file not found.")
        return

    questions = load_questions(str(questions_path))

    results = []

    print("=" * 60)
    print("Spatial-VLM Agent Evaluation")
    print("=" * 60)

    for q in questions:
        image_path = image_dir / q["image"]

        if not image_path.exists():
            print(f"[SKIP] {q['id']}: Image not found - {q['image']}")
            continue

        print(f"\n[TEST] {q['id']}: {q['question']}")

        try:
            answer, scene_graph, trace = run_agent(
                image_path=str(image_path),
                question=q["question"],
            )

            is_correct = check_answer(answer, q["ground_truth"])
            status = "PASS" if is_correct else "FAIL"

            print(f"  Answer: {answer[:80]}...")
            print(f"  Expected: {q['ground_truth']}")
            print(f"  Status: {status}")

            results.append({
                "id": q["id"],
                "status": status,
                "correct": is_correct,
            })

        except Exception as e:
            print(f"  Error: {e}")
            results.append({
                "id": q["id"],
                "status": "ERROR",
                "correct": False,
            })

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")

    print("\n" + "=" * 60)
    print("Evaluation Summary")
    print("=" * 60)
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    print(f"Accuracy: {passed / total * 100:.1f}%")
    print("=" * 60)

    # Save results
    output_path = Path("data/evaluation/results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
