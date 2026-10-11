package com.amazon.clone.analytics.event;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.List;
import java.util.Map;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class OrderCreatedEvent {
    private String eventId;
    private String orderId;
    private String userId;
    private Map<String, Object> order;
    private Instant timestamp;

    public Number totalAmount() {
        if (order == null) return 0;
        Object t = order.get("totalAmount");
        return t instanceof Number ? (Number) t : 0;
    }

    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> items() {
        if (order == null) return List.of();
        Object it = order.get("items");
        return it instanceof List ? (List<Map<String, Object>>) it : List.of();
    }
}
