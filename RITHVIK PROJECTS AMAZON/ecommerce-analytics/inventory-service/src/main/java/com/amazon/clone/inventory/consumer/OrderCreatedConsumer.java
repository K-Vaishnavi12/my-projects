package com.amazon.clone.inventory.consumer;

import com.amazon.clone.inventory.event.InventoryEvent;
import com.amazon.clone.inventory.event.OrderCreatedEvent;
import com.amazon.clone.inventory.service.InventoryService;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Saga pattern: consume order-created, try to reserve stock, emit inventory-reserved
 * (compensating action expected on failure by order-service).
 */
@Slf4j
@Component
public class OrderCreatedConsumer {

    private final InventoryService inventoryService;
    private final KafkaTemplate<String, Object> kafkaTemplate;
    private final Counter reservedCounter;
    private final Counter failedCounter;

    @Value("${app.kafka.topics.inventory-reserved}")
    private String reservedTopic;

    @Value("${app.kafka.topics.inventory-failed}")
    private String failedTopic;

    public OrderCreatedConsumer(InventoryService inventoryService,
                                KafkaTemplate<String, Object> kafkaTemplate,
                                MeterRegistry registry) {
        this.inventoryService = inventoryService;
        this.kafkaTemplate = kafkaTemplate;
        this.reservedCounter = Counter.builder("inventory.reserved").register(registry);
        this.failedCounter = Counter.builder("inventory.failed").register(registry);
    }

    @KafkaListener(topics = "${app.kafka.topics.order-created}", groupId = "inventory-service-group")
    public void onOrderCreated(OrderCreatedEvent event) {
        log.info("Received order-created: orderId={} userId={}", event.getOrderId(), event.getUserId());

        List<Map<String, Object>> items = event.getItems();
        String err = inventoryService.tryReserve(items);

        InventoryEvent out;
        String topic;
        if (err == null) {
            out = InventoryEvent.builder()
                    .eventId(UUID.randomUUID().toString())
                    .orderId(event.getOrderId())
                    .userId(event.getUserId())
                    .status("RESERVED")
                    .reservedProducts(items.stream()
                            .map(i -> String.valueOf(i.get("productId")))
                            .collect(Collectors.toList()))
                    .timestamp(Instant.now())
                    .build();
            topic = reservedTopic;
            reservedCounter.increment();
            log.info("RESERVED stock for order {}", event.getOrderId());
        } else {
            out = InventoryEvent.builder()
                    .eventId(UUID.randomUUID().toString())
                    .orderId(event.getOrderId())
                    .userId(event.getUserId())
                    .status("FAILED")
                    .reason(err)
                    .timestamp(Instant.now())
                    .build();
            topic = failedTopic;
            failedCounter.increment();
            log.warn("FAILED to reserve stock for order {}: {}", event.getOrderId(), err);
        }
        kafkaTemplate.send(topic, event.getUserId(), out);
    }
}
