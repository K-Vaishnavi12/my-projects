package com.amazon.clone.order.service;

import com.amazon.clone.order.event.OrderCreatedEvent;
import com.amazon.clone.order.exception.OrderNotFoundException;
import com.amazon.clone.order.model.CreateOrderRequest;
import com.amazon.clone.order.model.Order;
import com.amazon.clone.order.model.OrderItem;
import com.amazon.clone.order.repository.OrderRepository;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Slf4j
@Service
public class OrderService {

    private final OrderRepository orderRepository;
    private final KafkaTemplate<String, Object> kafkaTemplate;

    @Value("${app.kafka.topics.order-created}")
    private String orderCreatedTopic;

    public OrderService(OrderRepository orderRepository, KafkaTemplate<String, Object> kafkaTemplate) {
        this.orderRepository = orderRepository;
        this.kafkaTemplate = kafkaTemplate;
    }

    @CircuitBreaker(name = "orderService", fallbackMethod = "createOrderFallback")
    public Order createOrder(CreateOrderRequest request) {
        String orderId = "ORD-" + UUID.randomUUID().toString().substring(0, 12).toUpperCase();
        Instant now = Instant.now();

        BigDecimal total = request.getItems().stream()
                .map(item -> item.getPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        Order order = Order.builder()
                .orderId(orderId)
                .userId(request.getUserId())
                .items(request.getItems())
                .totalAmount(total)
                .status("PENDING")
                .shippingAddress(request.getShippingAddress())
                .createdAt(now)
                .updatedAt(now)
                .version(1L)
                .build();

        Order saved = orderRepository.save(order);
        log.info("Order created: {} for user: {} total: {}", orderId, request.getUserId(), total);

        // Publish event to Kafka (partition by userId => guarantees per-user ordering)
        OrderCreatedEvent event = new OrderCreatedEvent(
                UUID.randomUUID().toString(), orderId, request.getUserId(), saved, now);
        kafkaTemplate.send(orderCreatedTopic, request.getUserId(), event);
        log.info("Published OrderCreatedEvent to topic: {}", orderCreatedTopic);

        return saved;
    }

    public Order createOrderFallback(CreateOrderRequest request, Throwable t) {
        log.error("Circuit breaker OPEN - createOrder failed", t);
        throw new RuntimeException("Order service temporarily unavailable, please retry");
    }

    @Cacheable(value = "orders", key = "#orderId + ':' + #userId")
    public Order getOrder(String orderId, String userId) {
        log.debug("Cache MISS - fetching from DynamoDB: {}", orderId);
        return orderRepository.findById(orderId, userId)
                .orElseThrow(() -> new OrderNotFoundException("Order not found: " + orderId));
    }

    @CacheEvict(value = "orders", key = "#orderId + ':' + #userId")
    public Order updateStatus(String orderId, String userId, String newStatus) {
        Order order = orderRepository.findById(orderId, userId)
                .orElseThrow(() -> new OrderNotFoundException("Order not found: " + orderId));
        order.setStatus(newStatus);
        order.setUpdatedAt(Instant.now());
        order.setVersion(order.getVersion() + 1);
        return orderRepository.save(order);
    }
}
