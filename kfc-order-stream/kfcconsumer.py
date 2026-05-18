import json
import logging
import signal
import time

from confluent_kafka import Consumer, Producer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("kfc-consumer")

KFC_TOPIC = "kfc-orders"
DLQ_TOPIC = "kfc-orders.dlq"

consumer_config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "kfc-kitchen",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
    "client.id": "kfc-kitchen-1",
}

dlq_producer_config = {
    "bootstrap.servers": "localhost:9092",
    "acks": "all",
    "enable.idempotence": True,
    "client.id": "kfc-kitchen-dlq",
}

consumer = Consumer(consumer_config)
dlq_producer = Producer(dlq_producer_config)
consumer.subscribe([KFC_TOPIC])

running = True


def _stop(signum, _frame):
    global running
    log.info("🔴 Received signal %s, stopping consumer...", signum)
    running = False


signal.signal(signal.SIGINT, _stop)
try:
    signal.signal(signal.SIGTERM, _stop)
except (AttributeError, ValueError):
    pass


def send_to_dlq(msg, error):
    headers = [
        ("error", str(error).encode("utf-8")),
        ("source_topic", msg.topic().encode("utf-8")),
        ("source_partition", str(msg.partition()).encode("utf-8")),
        ("source_offset", str(msg.offset()).encode("utf-8")),
    ]
    try:
        dlq_producer.produce(
            topic=DLQ_TOPIC,
            key=msg.key(),
            value=msg.value(),
            headers=headers,
        )
        dlq_producer.poll(0)
    except Exception as e:
        log.exception("‼️ Failed to publish poison message to DLQ: %s", e)


def _format_addon(a):
    if isinstance(a, dict):
        return f"{a.get('name', '?')} (AED {a.get('price_aed', 0)})"
    return str(a)


def handle_order(msg):
    order = json.loads(msg.value().decode("utf-8"))

    branch = order.get("branch", "Unknown")
    order_type = order.get("type", "Unknown")
    customer = order.get("customer_name", "Unknown")
    phone = order.get("phone_number", "N/A")
    items = order.get("items", [])
    order_id = order.get("order_id", "?")
    total_aed = order.get("total_aed", 0)

    log.info("=" * 90)
    log.info("🍗 New KFC order from 🏬 %s", branch)
    log.info("   Type     : %s", order_type)
    log.info("   Order ID : %s", order_id)
    log.info("   Customer : %s", customer)
    log.info("   Phone    : %s", phone)
    log.info("   Items    : %d", len(items))
    for i, item in enumerate(items, start=1):
        name = item.get("name", "Unknown")
        price = item.get("price_aed", 0)
        addons = item.get("addons", [])
        tag = " 🎁 DEAL" if item.get("is_deal") else ""
        if addons:
            addons_str = ", ".join(_format_addon(a) for a in addons)
        else:
            addons_str = "no add-ons"
        log.info("     %d. %s (AED %d)%s  →  %s", i, name, price, tag, addons_str)
    log.info("   💰 TOTAL : AED %d", total_aed)
    log.info(
        "   [partition %d | offset %d | key %s]",
        msg.partition(),
        msg.offset(),
        msg.key().decode("utf-8") if msg.key() else None,
    )


log.info("🟢 KFC kitchen consumer running on '%s' (group=%s). SIGINT/SIGTERM to stop.",
         KFC_TOPIC, consumer_config["group.id"])

processed = 0
dlq_count = 0
window_start = time.monotonic()
THROUGHPUT_WINDOW = 10

try:
    while running:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            log.error("Kafka consumer error: %s", msg.error())
            continue

        try:
            handle_order(msg)
        except Exception as e:
            dlq_count += 1
            raw = msg.value()
            log.exception(
                "☠️ Poison message at offset %d, value=%r, forwarding to DLQ: %s",
                msg.offset(), raw[:500] if raw else raw, e,
            )
            send_to_dlq(msg, e)

        try:
            consumer.commit(message=msg, asynchronous=False)
        except Exception as e:
            log.exception("Failed to commit offset %d: %s", msg.offset(), e)

        processed += 1
        if processed % THROUGHPUT_WINDOW == 0:
            elapsed = time.monotonic() - window_start
            rate = THROUGHPUT_WINDOW / elapsed if elapsed > 0 else 0
            log.info(
                "📈 Throughput: %d processed (%d to DLQ), %.2f msg/sec",
                processed, dlq_count, rate,
            )
            window_start = time.monotonic()

finally:
    log.info("Flushing DLQ producer and closing consumer...")
    dlq_producer.flush(timeout=10)
    consumer.close()
    log.info("🏁 Consumer closed cleanly. Processed=%d, DLQ=%d", processed, dlq_count)
