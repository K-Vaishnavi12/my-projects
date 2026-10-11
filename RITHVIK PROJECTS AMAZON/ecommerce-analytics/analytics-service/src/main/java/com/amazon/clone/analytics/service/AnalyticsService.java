package com.amazon.clone.analytics.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.*;

/**
 * Sliding-window analytics stored entirely in Redis.
 * - orders per minute (sorted set, timestamp-scored)
 * - revenue per minute (hash by minute bucket)
 * - top products (sorted set by units sold)
 *
 * This is the same pattern used by Twitter/X for real-time trending.
 */
@Slf4j
@Service
public class AnalyticsService {

    private static final String ORDER_TIMES_ZSET = "analytics:order_times";
    private static final String REVENUE_HASH = "analytics:revenue_per_min";
    private static final String TOP_PRODUCTS_ZSET = "analytics:top_products";
    private static final String TOTAL_ORDERS_KEY = "analytics:total_orders";
    private static final String TOTAL_REVENUE_KEY = "analytics:total_revenue";

    private final StringRedisTemplate redis;

    public AnalyticsService(StringRedisTemplate redis) { this.redis = redis; }

    public void record(String orderId, double amount, List<Map<String, Object>> items) {
        long now = Instant.now().getEpochSecond();
        long minuteBucket = now / 60;

        redis.opsForZSet().add(ORDER_TIMES_ZSET, orderId + ":" + now, now);
        redis.opsForHash().increment(REVENUE_HASH, String.valueOf(minuteBucket), (long) amount);
        redis.opsForValue().increment(TOTAL_ORDERS_KEY, 1);
        redis.opsForValue().increment(TOTAL_REVENUE_KEY, (long) amount);

        for (Map<String, Object> item : items) {
            String pid = String.valueOf(item.get("productId"));
            long qty = ((Number) item.getOrDefault("quantity", 0)).longValue();
            redis.opsForZSet().incrementScore(TOP_PRODUCTS_ZSET, pid, qty);
        }
        log.debug("recorded order={} amount={}", orderId, amount);
    }

    /** orders in the last N seconds */
    public long ordersInLastSeconds(int seconds) {
        long now = Instant.now().getEpochSecond();
        Long count = redis.opsForZSet().count(ORDER_TIMES_ZSET, now - seconds, now);
        return count == null ? 0 : count;
    }

    public long totalOrders() {
        String v = redis.opsForValue().get(TOTAL_ORDERS_KEY);
        return v == null ? 0 : Long.parseLong(v);
    }

    public long totalRevenue() {
        String v = redis.opsForValue().get(TOTAL_REVENUE_KEY);
        return v == null ? 0 : Long.parseLong(v);
    }

    public List<Map<String, Object>> topProducts(int n) {
        Set<ZSetOperations.TypedTuple<String>> top =
                redis.opsForZSet().reverseRangeWithScores(TOP_PRODUCTS_ZSET, 0, n - 1);
        List<Map<String, Object>> result = new ArrayList<>();
        if (top == null) return result;
        for (var t : top) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("productId", t.getValue());
            row.put("unitsSold", t.getScore());
            result.add(row);
        }
        return result;
    }

    /** Trim data older than 1 hour to keep memory bounded. */
    public void trim() {
        long cutoff = Instant.now().getEpochSecond() - 3600;
        Long removed = redis.opsForZSet().removeRangeByScore(ORDER_TIMES_ZSET, 0, cutoff);
        if (removed != null && removed > 0) log.debug("trimmed {} old order entries", removed);
    }
}
