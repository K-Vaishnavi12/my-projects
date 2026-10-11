package com.amazon.clone.analytics.consumer;

import com.amazon.clone.analytics.event.OrderCreatedEvent;
import com.amazon.clone.analytics.service.AnalyticsService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class OrderEventConsumer {

    private final AnalyticsService analyticsService;

    public OrderEventConsumer(AnalyticsService analyticsService) {
        this.analyticsService = analyticsService;
    }

    @KafkaListener(topics = "${app.kafka.topics.order-created}", groupId = "analytics-service-group")
    public void onOrderCreated(OrderCreatedEvent event) {
        double amount = event.totalAmount().doubleValue();
        analyticsService.record(event.getOrderId(), amount, event.items());
        log.debug("analytics recorded orderId={}", event.getOrderId());
    }

    /** Every minute trim aged data to bound memory. */
    @Scheduled(fixedRate = 60_000)
    public void trim() { analyticsService.trim(); }
}
