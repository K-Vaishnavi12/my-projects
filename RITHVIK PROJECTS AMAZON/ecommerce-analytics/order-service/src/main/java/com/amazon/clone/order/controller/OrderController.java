package com.amazon.clone.order.controller;

import com.amazon.clone.order.model.CreateOrderRequest;
import com.amazon.clone.order.model.Order;
import com.amazon.clone.order.service.OrderService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping
    public ResponseEntity<Order> createOrder(@Valid @RequestBody CreateOrderRequest request) {
        Order order = orderService.createOrder(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(order);
    }

    @GetMapping("/{orderId}/user/{userId}")
    public ResponseEntity<Order> getOrder(@PathVariable String orderId, @PathVariable String userId) {
        return ResponseEntity.ok(orderService.getOrder(orderId, userId));
    }

    @PatchMapping("/{orderId}/user/{userId}/status")
    public ResponseEntity<Order> updateStatus(@PathVariable String orderId,
                                              @PathVariable String userId,
                                              @RequestBody Map<String, String> body) {
        return ResponseEntity.ok(orderService.updateStatus(orderId, userId, body.get("status")));
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("status", "UP", "service", "order-service"));
    }
}
