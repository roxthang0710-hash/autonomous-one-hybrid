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
    return min(topics, key=lambda topic: counts[topic])


def should_pause_scheduled(history, threshold=8):
    """Stop generating more proposals until the owner reviews pending ideas."""
    return sum(
        item.get("approval_status") == "pending" for item in history
    ) >= threshold
