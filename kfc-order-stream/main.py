import json
import logging
import random
import signal
import time

from confluent_kafka import Producer

from kfcproducer import generate_order

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("kfc-producer")

KFC_TOPIC = "kfc-orders"

producer_config = {
    "bootstrap.servers": "localhost:9092",
    "acks": "all",
    "enable.idempotence": True,
    "retries": 10_000_000,
    "max.in.flight.requests.per.connection": 5,
    "compression.type": "lz4",
    "linger.ms": 20,
    "client.id": "kfc-producer",
}

producer = Producer(producer_config)

running = True


def _stop(signum, _frame):
    global running
    log.info("🔴 Received signal %s, stopping producer...", signum)
    running = False


signal.signal(signal.SIGINT, _stop)
try:
    signal.signal(signal.SIGTERM, _stop)
except (AttributeError, ValueError):
    pass


def delivery_report(err, msg):
    if err:
        try:
            order_id = json.loads(msg.value().decode("utf-8")).get("order_id", "?")
        except Exception:
            order_id = "?"
        log.error("❌ Delivery failed for order_id=%s: %s", order_id, err)
    else:
        log.info(
            "✅ Delivered to %s [partition %d | offset %d]",
            msg.topic(),
            msg.partition(),
            msg.offset(),
        )


def main(avg_delay=3.0, throughput_window=10):
    log.info("🟢 KFC order producer started on topic '%s'. SIGINT/SIGTERM to stop.", KFC_TOPIC)
    sent = 0
    window_start = time.monotonic()

    while running:
        order = generate_order()
        value = json.dumps(order).encode("utf-8")
        key = order["branch"].encode("utf-8")

        while running:
            try:
                producer.produce(
                    topic=KFC_TOPIC,
                    key=key,
                    value=value,
                    callback=delivery_report,
                )
                break
            except BufferError:
                log.warning("Producer queue full, draining...")
                producer.poll(1)

        producer.poll(0)

        log.info(
            "📤 %s | %s | %s | %s | %d item(s) | total: AED %d",
            order["branch"],
            order["type"],
            order["customer_name"],
            order["phone_number"],
            len(order["items"]),
            order["total_aed"],
        )

        sent += 1
        if sent % throughput_window == 0:
            elapsed = time.monotonic() - window_start
            rate = throughput_window / elapsed if elapsed > 0 else 0
            log.info("📈 Throughput: %d orders sent, %.2f orders/sec", sent, rate)
            window_start = time.monotonic()

        time.sleep(random.expovariate(1 / avg_delay))

    log.info("Flushing pending messages...")
    remaining = producer.flush(timeout=10)
    if remaining > 0:
        log.error("🏁 Shutdown with %d messages still pending in queue", remaining)
    else:
        log.info("🏁 Producer shut down cleanly. Total sent: %d", sent)


if __name__ == "__main__":
    main()
