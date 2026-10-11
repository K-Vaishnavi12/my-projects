package com.amazon.clone.inventory.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

/**
 * Inventory backed by Redis. Uses Redis atomic DECRBY for optimistic reservation.
 * Key: stock:{productId}  Value: integer stock count.
 */
@Slf4j
@Service
public class InventoryService {

    private static final String STOCK_PREFIX = "stock:";

    private final StringRedisTemplate redis;

    @Autowired
    public InventoryService(StringRedisTemplate redis) {
        this.redis = redis;
    }

    /**
     * Seed initial stock on startup so demos work out of the box.
     */
    @EventListener(ApplicationReadyEvent.class)
    public void seedStock() {
        Map<String, Integer> initial = Map.of(
                "P001", 100,
                "P002", 500,
                "P003", 50,
                "P004", 200
        );
        initial.forEach((pid, qty) -> {
            String k = STOCK_PREFIX + pid;
            if (Boolean.FALSE.equals(redis.hasKey(k))) {
                redis.opsForValue().set(k, String.valueOf(qty));
                log.info("[SEED] {}={}", pid, qty);
            }
        });
    }

    public long getStock(String productId) {
        String v = redis.opsForValue().get(STOCK_PREFIX + productId);
        return v == null ? 0 : Long.parseLong(v);
    }

    /**
     * Try to atomically reserve inventory for all items. Returns null on success,
     * or an error message on failure (with compensating rollback).
     */
    public String tryReserve(List<Map<String, Object>> items) {
        var reservedSoFar = new java.util.ArrayList<Map.Entry<String, Long>>();
        for (Map<String, Object> item : items) {
            String pid = String.valueOf(item.get("productId"));
            long qty = ((Number) item.getOrDefault("quantity", 0)).longValue();

            Long remaining = redis.opsForValue().decrement(STOCK_PREFIX + pid, qty);
            if (remaining == null || remaining < 0) {
                // Not enough stock: rollback this one + all previously reserved
                redis.opsForValue().increment(STOCK_PREFIX + pid, qty);
                reservedSoFar.forEach(e -> redis.opsForValue().increment(STOCK_PREFIX + e.getKey(), e.getValue()));
                return "Insufficient stock for product " + pid;
            }
            reservedSoFar.add(Map.entry(pid, qty));
            log.debug("Reserved {} x {} (remaining={})", qty, pid, remaining);
        }
        return null;
    }
}
