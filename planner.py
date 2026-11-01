"""Low-cost scheduling: rotate research topics and stop creating a queue of unreviewed ideas."""
DEFAULT_TOPICS = (
    "small business workflow automation",
    "marketing reporting pain points",
    "digital products for freelancers",
    "independent business tools",
)


def choose_topic(history, topics=DEFAULT_TOPICS):
    """Choose the least explored topic (use longest-idle position as tie-break)."""
    counts = {topic: 0 for topic in topics}
    for item in history:
        topic = item.get("topic")
        if topic in counts:
            counts[topic] += 1
    if not topics:
        raise ValueError("At least one topic is required")
    # History is newest-first; a larger position means a longer idle period.
    last_seen = {topic: len(history) for topic in topics}
    for index, item in enumerate(history):
        topic = item.get("topic")
        if topic in last_seen and last_seen[topic] == len(history):
            last_seen[topic] = index
    return min(topics, key=lambda topic: (counts[topic], -last_seen[topic]))


def should_pause_scheduled(history, threshold=8):
    """Stop generating more proposals until the owner reviews pending ideas."""
    return sum(
        item.get("approval_status") == "pending" for item in history
    ) >= threshold


def build_tasks(proposal, evaluation):
    """Bounded internal plan: never execute outreach or financial operations."""
    duplicate = evaluation.get('rubric', {}).get('novelty', {}).get('duplicate', False)
    return [
        {'position': 1, 'kind': 'review_evidence', 'status': 'pending',
         'description': 'Kiểm tra nguồn và giả thuyết; nguồn công khai chưa chứng minh nhu cầu.'},
        {'position': 2, 'kind': 'differentiate' if duplicate else 'prepare_simulation',
         'status': 'pending', 'description': 'Làm rõ điểm mới trước khi tiếp tục.' if duplicate else
         'Chọn giả định đầu vào cho thử nghiệm giả lập, không tiếp cận khách hàng.'},
        {'position': 3, 'kind': 'owner_review', 'status': 'blocked',
         'description': 'Chờ chủ sở hữu duyệt mọi hoạt động thực tế.'},
    ]
