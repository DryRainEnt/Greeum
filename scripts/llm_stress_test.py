#!/usr/bin/env python3
"""
Greeum LLM Context Classifier - Large Scale Stress Test
Estimated runtime: 2-3 hours
"""

import json
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from greeum.core.context_classifier import get_context_classifier

# =============================================================================
# Configuration
# =============================================================================
OUTPUT_DIR = Path(__file__).parent.parent / "test_results"
OUTPUT_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULTS_FILE = OUTPUT_DIR / f"stress_test_{TIMESTAMP}.json"
SUMMARY_FILE = OUTPUT_DIR / f"stress_test_{TIMESTAMP}_summary.txt"
LOG_FILE = OUTPUT_DIR / f"stress_test_{TIMESTAMP}.log"

# Test configuration
TARGET_DURATION_HOURS = 2.5
CHECKPOINT_INTERVAL = 300  # Save checkpoint every 5 minutes
CONSISTENCY_REPEATS = 5

# =============================================================================
# Template-based Test Data Generation
# =============================================================================

TEMPLATES = {
    "A": {  # Work/Project
        "patterns": [
            "{action} {target}을/를 {verb}.",
            "{project} 프로젝트 {status}.",
            "{tool}로 {task} 작업 중.",
            "팀 {meeting}에서 {topic} 논의.",
            "{system} {component} {action_past}.",
            "{dev_action} 완료하고 {next_action}.",
            "클라이언트 요청으로 {feature} {dev_status}.",
            "{code_action} 후 테스트 {test_result}.",
            "배포 {deploy_status}, {env} 환경.",
            "{review_type} 리뷰 {review_action}.",
        ],
        "fills": {
            "action": ["구현", "수정", "리팩토링", "최적화", "디버깅", "설계", "분석", "테스트"],
            "target": ["API", "서버", "클라이언트", "데이터베이스", "캐시", "로직", "모듈", "함수"],
            "verb": ["완료했다", "진행 중", "시작했다", "마무리했다"],
            "project": ["Greeum", "백엔드", "프론트엔드", "인프라", "ML 파이프라인", "데이터"],
            "status": ["진행 중", "완료", "시작", "마무리 단계", "테스트 중"],
            "tool": ["Docker", "Kubernetes", "Git", "Jenkins", "Terraform", "VS Code"],
            "task": ["배포", "설정", "마이그레이션", "모니터링", "자동화"],
            "meeting": ["미팅", "스탠드업", "회의", "리뷰"],
            "topic": ["진행 상황", "이슈", "일정", "기술 스택", "아키텍처"],
            "system": ["인증", "결제", "알림", "검색", "추천"],
            "component": ["시스템", "서비스", "모듈", "API"],
            "action_past": ["개선", "수정", "추가", "제거", "업데이트"],
            "dev_action": ["코드 작성", "버그 수정", "기능 추가", "성능 개선"],
            "next_action": ["PR 올림", "코드 리뷰 요청", "테스트 작성", "문서화"],
            "feature": ["새 기능", "버그 픽스", "UI 개선", "API 변경"],
            "dev_status": ["개발 중", "완료", "검토 중", "배포 대기"],
            "code_action": ["커밋", "푸시", "머지", "리베이스"],
            "test_result": ["통과", "실패 후 수정", "진행 중"],
            "deploy_status": ["완료", "진행 중", "롤백", "대기"],
            "env": ["개발", "스테이징", "프로덕션", "테스트"],
            "review_type": ["코드", "설계", "PR", "아키텍처"],
            "review_action": ["완료", "진행 중", "요청", "피드백 반영"],
        }
    },
    "B": {  # Personal/Daily
        "patterns": [
            "오늘 {person}와/과 {activity}.",
            "{time}에 {place}에서 {food} 먹었다.",
            "{weather} 날씨라서 {outdoor_activity}.",
            "주말에 {weekend_activity}.",
            "{feeling} 기분이라 {mood_activity}.",
            "{person}한테 {communication} 받았다.",
            "집에서 {home_activity}.",
            "{entertainment} 보면서 {snack} 먹음.",
            "오랜만에 {hobby} 했다.",
            "{exercise} 하고 {after_exercise}.",
        ],
        "fills": {
            "person": ["친구", "가족", "동생", "부모님", "연인", "동료"],
            "activity": ["저녁 식사", "영화 관람", "카페 방문", "쇼핑", "산책", "게임"],
            "time": ["점심", "저녁", "아침", "새벽", "오후"],
            "place": ["맛집", "카페", "레스토랑", "편의점", "집"],
            "food": ["치킨", "피자", "라면", "삼겹살", "초밥", "파스타", "햄버거"],
            "weather": ["맑은", "흐린", "비오는", "눈오는", "따뜻한", "시원한"],
            "outdoor_activity": ["산책했다", "조깅했다", "자전거 탔다", "드라이브 갔다"],
            "weekend_activity": ["여행 다녀왔다", "집에서 쉬었다", "친구 만났다", "청소했다"],
            "feeling": ["좋은", "피곤한", "설레는", "우울한", "편안한"],
            "mood_activity": ["음악 들었다", "산책했다", "잠 잤다", "게임했다"],
            "communication": ["연락", "전화", "메시지", "선물"],
            "home_activity": ["청소", "요리", "빨래", "정리", "휴식"],
            "entertainment": ["드라마", "영화", "유튜브", "넷플릭스", "예능"],
            "snack": ["과자", "팝콘", "아이스크림", "과일"],
            "hobby": ["게임", "독서", "그림 그리기", "악기 연주", "요리"],
            "exercise": ["헬스", "러닝", "수영", "요가", "등산"],
            "after_exercise": ["샤워했다", "휴식했다", "밥 먹었다", "스트레칭했다"],
        }
    },
    "C": {  # Learning/Knowledge
        "patterns": [
            "{subject} {study_action}.",
            "{resource}에서 {topic} 배웠다.",
            "{concept} 개념 {understanding}.",
            "오늘 {learned_thing} 알게 됨.",
            "{course} 강의 {course_status}.",
            "{book} 책 읽는 중, {chapter} 부분.",
            "{lang} 문법 {lang_action}.",
            "{field} 관련 {material} 정리.",
            "알고리즘 문제 {algo_count}개 {algo_status}.",
            "{cert} 자격증 {cert_action}.",
        ],
        "fills": {
            "subject": ["Python", "JavaScript", "머신러닝", "데이터분석", "영어", "수학"],
            "study_action": ["공부 중", "복습했다", "정리했다", "실습했다"],
            "resource": ["강의", "책", "블로그", "문서", "튜토리얼", "유튜브"],
            "topic": ["새로운 기능", "핵심 개념", "실전 예제", "베스트 프랙티스"],
            "concept": ["객체지향", "함수형", "비동기", "동시성", "디자인 패턴"],
            "understanding": ["이해함", "어려움", "복습 필요", "마스터"],
            "learned_thing": ["새로운 라이브러리", "최적화 기법", "버그 해결법", "설계 패턴"],
            "course": ["온라인", "오프라인", "부트캠프", "대학"],
            "course_status": ["수강 중", "완료", "시작", "복습"],
            "book": ["기술", "교양", "전공", "자기계발"],
            "chapter": ["초반", "중반", "후반", "마무리"],
            "lang": ["영어", "일본어", "중국어", "한국어", "프랑스어"],
            "lang_action": ["공부", "연습", "복습", "암기"],
            "field": ["AI", "클라우드", "보안", "네트워크", "데이터베이스"],
            "material": ["논문", "문서", "자료", "노트"],
            "algo_count": ["3", "5", "10", "1", "7"],
            "algo_status": ["풀었다", "도전 중", "복습", "실패 후 재도전"],
            "cert": ["AWS", "정보처리기사", "SQLD", "토익", "OPIC"],
            "cert_action": ["준비 중", "취득", "공부 시작", "시험 예정"],
        }
    }
}

EDGE_CASES = [
    ("", "edge"),
    (".", "edge"),
    ("...", "edge"),
    ("ㅋㅋㅋ", "edge"),
    ("ㅠㅠ", "edge"),
    ("오늘", "edge"),
    ("좋아", "edge"),
    ("123", "edge"),
    ("!@#$%", "edge"),
    ("hello", "edge"),
    ("こんにちは", "edge"),
    ("你好", "edge"),
    ("🎉🎊🎁", "edge"),
    ("a" * 500, "edge"),  # Very long
    ("오늘 코딩하면서 친구랑 통화하고 새로운 개념도 배웠다", "edge"),  # Mixed
]


def generate_sentence(category: str) -> str:
    """Generate a random sentence for the given category."""
    template_data = TEMPLATES[category]
    pattern = random.choice(template_data["patterns"])
    fills = template_data["fills"]

    # Replace placeholders
    result = pattern
    for key, values in fills.items():
        placeholder = "{" + key + "}"
        if placeholder in result:
            result = result.replace(placeholder, random.choice(values), 1)

    return result


def generate_test_dataset(count: int) -> list:
    """Generate a balanced test dataset."""
    dataset = []
    per_category = count // 3

    for category in ["A", "B", "C"]:
        for _ in range(per_category):
            sentence = generate_sentence(category)
            dataset.append({"content": sentence, "expected": category, "type": "generated"})

    # Add edge cases
    for content, case_type in EDGE_CASES:
        dataset.append({"content": content, "expected": "?", "type": case_type})

    random.shuffle(dataset)
    return dataset


# =============================================================================
# Test Runner
# =============================================================================

def log(message: str):
    """Log message to file and stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def save_checkpoint(results: dict, stats: dict):
    """Save intermediate results."""
    checkpoint = {
        "timestamp": datetime.now().isoformat(),
        "stats": stats,
        "results_count": len(results.get("classifications", [])),
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"checkpoint": checkpoint, "results": results}, f, ensure_ascii=False, indent=2)

    log(f"Checkpoint saved: {stats['total_classifications']} classifications")


def run_stress_test():
    """Main stress test runner."""
    log("=" * 70)
    log("Greeum LLM Context Classifier - Large Scale Stress Test")
    log("=" * 70)
    log(f"Target duration: {TARGET_DURATION_HOURS} hours")
    log(f"Results will be saved to: {RESULTS_FILE}")
    log("")

    # Initialize classifier
    classifier = get_context_classifier()
    if not classifier.is_available():
        log("ERROR: LLM classifier not available!")
        return

    log(f"LLM server: {classifier.llm_url}")
    log("")

    # Generate initial dataset
    log("Generating test dataset...")
    dataset = generate_test_dataset(5000)
    log(f"Generated {len(dataset)} test cases")
    log("")

    # Initialize results
    results = {
        "classifications": [],
        "consistency_tests": [],
        "timing_samples": [],
        "errors": [],
    }

    stats = {
        "total_classifications": 0,
        "correct": 0,
        "incorrect": 0,
        "edge_cases": 0,
        "total_time_ms": 0,
        "min_time_ms": float("inf"),
        "max_time_ms": 0,
        "errors": 0,
        "by_category": {"A": {"total": 0, "correct": 0}, "B": {"total": 0, "correct": 0}, "C": {"total": 0, "correct": 0}},
        "consistency_failures": 0,
    }

    start_time = time.time()
    last_checkpoint = start_time
    target_end = start_time + (TARGET_DURATION_HOURS * 3600)

    log("Starting stress test...")
    log("")

    iteration = 0

    while time.time() < target_end:
        iteration += 1

        # Phase 1: Classification accuracy test
        test_case = random.choice(dataset)
        content = test_case["content"]
        expected = test_case["expected"]

        try:
            t_start = time.time()
            result = classifier.classify(content)
            t_elapsed = (time.time() - t_start) * 1000

            stats["total_classifications"] += 1
            stats["total_time_ms"] += t_elapsed
            stats["min_time_ms"] = min(stats["min_time_ms"], t_elapsed)
            stats["max_time_ms"] = max(stats["max_time_ms"], t_elapsed)

            if expected == "?":
                stats["edge_cases"] += 1
            elif result.slot == expected:
                stats["correct"] += 1
                stats["by_category"][expected]["correct"] += 1
                stats["by_category"][expected]["total"] += 1
            else:
                stats["incorrect"] += 1
                stats["by_category"][expected]["total"] += 1
                results["classifications"].append({
                    "content": content[:100],
                    "expected": expected,
                    "got": result.slot,
                    "time_ms": t_elapsed,
                    "fallback": result.fallback_used,
                })

            # Sample timing data periodically
            if iteration % 100 == 0:
                results["timing_samples"].append({
                    "iteration": iteration,
                    "time_ms": t_elapsed,
                    "timestamp": time.time() - start_time,
                })

        except Exception as e:
            stats["errors"] += 1
            results["errors"].append({
                "iteration": iteration,
                "content": content[:50],
                "error": str(e),
            })

        # Phase 2: Consistency test (every 500 iterations)
        if iteration % 500 == 0:
            test_sentence = generate_sentence(random.choice(["A", "B", "C"]))
            slots = []
            for _ in range(CONSISTENCY_REPEATS):
                try:
                    r = classifier.classify(test_sentence)
                    slots.append(r.slot)
                except:
                    slots.append("ERROR")

            if len(set(slots)) > 1:
                stats["consistency_failures"] += 1
                results["consistency_tests"].append({
                    "sentence": test_sentence[:50],
                    "results": slots,
                    "iteration": iteration,
                })

        # Progress update every 1000 iterations
        if iteration % 1000 == 0:
            elapsed_hours = (time.time() - start_time) / 3600
            remaining_hours = (target_end - time.time()) / 3600
            accuracy = stats["correct"] / max(1, stats["correct"] + stats["incorrect"]) * 100
            avg_time = stats["total_time_ms"] / max(1, stats["total_classifications"])

            log(f"Progress: {iteration} iterations | "
                f"Accuracy: {accuracy:.1f}% | "
                f"Avg time: {avg_time:.1f}ms | "
                f"Elapsed: {elapsed_hours:.1f}h | "
                f"Remaining: {remaining_hours:.1f}h")

        # Save checkpoint periodically
        if time.time() - last_checkpoint > CHECKPOINT_INTERVAL:
            save_checkpoint(results, stats)
            last_checkpoint = time.time()

    # Final save
    total_time = time.time() - start_time

    stats["total_time_seconds"] = total_time
    stats["avg_time_ms"] = stats["total_time_ms"] / max(1, stats["total_classifications"])
    stats["accuracy"] = stats["correct"] / max(1, stats["correct"] + stats["incorrect"]) * 100
    stats["throughput"] = stats["total_classifications"] / total_time

    # Category-wise accuracy
    for cat in ["A", "B", "C"]:
        cat_stats = stats["by_category"][cat]
        cat_stats["accuracy"] = cat_stats["correct"] / max(1, cat_stats["total"]) * 100

    save_checkpoint(results, stats)

    # Write summary
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("GREEUM LLM CLASSIFIER STRESS TEST - FINAL SUMMARY\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Test completed at: {datetime.now().isoformat()}\n")
        f.write(f"Total duration: {total_time/3600:.2f} hours\n\n")

        f.write("OVERALL STATISTICS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total classifications: {stats['total_classifications']:,}\n")
        f.write(f"Correct: {stats['correct']:,}\n")
        f.write(f"Incorrect: {stats['incorrect']:,}\n")
        f.write(f"Edge cases: {stats['edge_cases']:,}\n")
        f.write(f"Errors: {stats['errors']:,}\n")
        f.write(f"Overall accuracy: {stats['accuracy']:.2f}%\n\n")

        f.write("PERFORMANCE\n")
        f.write("-" * 40 + "\n")
        f.write(f"Average response time: {stats['avg_time_ms']:.2f}ms\n")
        f.write(f"Min response time: {stats['min_time_ms']:.2f}ms\n")
        f.write(f"Max response time: {stats['max_time_ms']:.2f}ms\n")
        f.write(f"Throughput: {stats['throughput']:.2f} req/sec\n\n")

        f.write("CATEGORY-WISE ACCURACY\n")
        f.write("-" * 40 + "\n")
        for cat, cat_stats in stats["by_category"].items():
            f.write(f"  {cat}: {cat_stats['accuracy']:.2f}% ({cat_stats['correct']}/{cat_stats['total']})\n")
        f.write("\n")

        f.write("CONSISTENCY\n")
        f.write("-" * 40 + "\n")
        f.write(f"Consistency failures: {stats['consistency_failures']}\n\n")

        f.write("FILES\n")
        f.write("-" * 40 + "\n")
        f.write(f"Full results: {RESULTS_FILE}\n")
        f.write(f"Log file: {LOG_FILE}\n")

    log("")
    log("=" * 70)
    log("STRESS TEST COMPLETED")
    log("=" * 70)
    log(f"Total classifications: {stats['total_classifications']:,}")
    log(f"Accuracy: {stats['accuracy']:.2f}%")
    log(f"Throughput: {stats['throughput']:.2f} req/sec")
    log(f"Summary saved to: {SUMMARY_FILE}")


if __name__ == "__main__":
    run_stress_test()
