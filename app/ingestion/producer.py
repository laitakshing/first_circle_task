# app/ingestion/producer.py

import json
import time
import os
from kafka import KafkaProducer

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transactions")
INPUT_FILE = os.getenv("INPUT_FILE", "sample_data/sample_kafka_messages.jsonl")


def load_and_send(file_path: str, broker: str = KAFKA_BROKER, topic: str = KAFKA_TOPIC):
    producer = KafkaProducer(
        bootstrap_servers=[broker],
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    with open(file_path, "r") as f:
        for line in f:
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                print(f"[Producer] skipping invalid JSON line: {line!r}")
                continue

            print(f"[Producer] Sending {evt.get('transaction_id')} …")
            producer.send(topic, evt)
            producer.flush()
            time.sleep(0.5)  # small delay to simulate a real stream

    producer.close()


if __name__ == "__main__":
    load_and_send(INPUT_FILE)
